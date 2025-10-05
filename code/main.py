from settings import *
from player import Player
from sprites import *
from pytmx.util_pygame import load_pygame
from groups import AllSprites

from random import choice

class Game:
    def __init__(self):
        # setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Survivor')
        self.clock = pygame.time.Clock()
        self.running = True

        # groups
        self.all_sprites = AllSprites()
        self.collision_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        # gun timer
        self.can_shoot = True
        self.shoot_time = 0
        self.gun_cooldown = 100

        # enemy timer
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 300)
        self.spawn_positions = []

        # audio
        self.shoot_sound = pygame.mixer.Sound(join('audio', 'shoot.wav'))
        self.shoot_sound.set_volume(0.4)
        self.impact_sound = pygame.mixer.Sound(join('audio', 'impact.ogg'))
        self.music = pygame.mixer.Sound(join('audio', 'music.wav'))
        self.music.set_volume(0.3)
        self.music.play(loops = -1)

        # coin and upgrade system
        self.coins = 0
        self.upgrades = {
            'speed': 0,
            'enemy_slow': 0,
            'health': 0
        }
        self.upgrade_costs = {
            'speed': 5,
            'enemy_slow': 5,
            'health': 5
        }
        self.upgrade_menu = False

        # setup
        self.setup()
        self.load_images()

    def load_images(self):
        self.bullet_surf = pygame.image.load(join('images', 'gun', 'bullet.png')).convert_alpha()

        folders = list(walk(join('images', 'enemies')))[0][1]
        self.enemy_frames = {}
        for folder in folders:
            for folder_path, _, file_names in walk(join('images', 'enemies', folder)):
                self.enemy_frames[folder] = []
                for file_name in sorted(file_names, key = lambda name: int(name.split('.')[0])):
                    full_path = join(folder_path, file_name)
                    surf = pygame.image.load(full_path).convert_alpha()
                    self.enemy_frames[folder].append(surf)

    def input(self):
        if self.upgrade_menu:
            return
        if pygame.mouse.get_pressed()[0] and self.can_shoot:
            self.shoot_sound.play()
            pos = self.player.rect.center + self.gun.player_direction * 50
            Bullet(self.bullet_surf, pos, self.gun.player_direction, (self.all_sprites, self.bullet_sprites))
            self.can_shoot = False
            self.shoot_time = pygame.time.get_ticks()

    def gun_timer(self):
        if not self.can_shoot:
            current_time = pygame.time.get_ticks()
            if current_time - self.shoot_time >= self.gun_cooldown:
                self.can_shoot = True

    def setup(self):
        map = load_pygame(join('data', 'maps', 'world.tmx'))
        for x, y, image in map.get_layer_by_name('Ground').tiles():
            Sprite((x * TILE_SIZE,y * TILE_SIZE), image, self.all_sprites)
            
        for obj in map.get_layer_by_name('Objects'):
            CollisionSprite((obj.x, obj.y), obj.image, (self.all_sprites, self.collision_sprites))

        for obj in map.get_layer_by_name('Collisions'):
            CollisionSprite((obj.x, obj.y), pygame.Surface((obj.width, obj.height)), self.collision_sprites)

        for obj in map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                self.player = Player((obj.x,obj.y), self.all_sprites, self.collision_sprites)
                self.player.max_health = 100
                self.player.health = 100
                self.gun = Gun(self.player, self.all_sprites)
            else: 
                self.spawn_positions.append((obj.x, obj.y))

    def bullet_collision(self):
        if self.bullet_sprites:
            for bullet in self.bullet_sprites:
                collision_sprites = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
                if collision_sprites:
                    self.impact_sound.play()
                    for sprite in collision_sprites:
                        sprite.destroy()
                        self.coins += 3  # Award coins for each enemy killed
                    bullet.kill()

    def player_collision(self):
        if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
            self.running = False

    def draw_upgrade_menu(self, font):
        upgrades = [
            ('SPEED', 'speed', (255,255,255)),
            ('ENEMY SLOW', 'enemy_slow', (200,200,200)),
            ('HEALTH', 'health', (200,200,200))
        ]
        slider_width = 100
        slider_height = 400
        gap = 80

        menu_rect = pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.display_surface, (30, 30, 30), menu_rect)
        pygame.draw.rect(self.display_surface, (200, 200, 0), menu_rect, 8)

        total_width = len(upgrades) * slider_width + (len(upgrades) - 1) * gap
        start_x = (WINDOW_WIDTH - total_width) // 2
        start_y = (WINDOW_HEIGHT - slider_height) // 2

        max_level = 10

        for i, (label, key, color) in enumerate(upgrades):
            x = start_x + i * (slider_width + gap)
            slider_rect = pygame.Rect(x, start_y, slider_width, slider_height)
            pygame.draw.rect(self.display_surface, color, slider_rect, border_radius=12)
            pygame.draw.rect(self.display_surface, (0,0,0), slider_rect, 6, border_radius=12)

            line_x = x + slider_width // 2
            line_top = start_y + 30
            line_bottom = start_y + slider_height - 30
            pygame.draw.line(self.display_surface, (0,0,0), (line_x, line_top), (line_x, line_bottom), 6)

            level = min(self.upgrades[key], max_level)
            handle_y = line_bottom - int((line_bottom - line_top) * (level / max_level))
            pygame.draw.rect(self.display_surface, (255, 220, 0), (line_x - 24, handle_y - 12, 48, 24), border_radius=8)

            value_surf = font.render(str(level), True, (0,0,0))
            value_rect = value_surf.get_rect(center=(line_x, start_y + slider_height - 15))
            self.display_surface.blit(value_surf, value_rect)

            cost = self.upgrade_costs[key]
            if level >= max_level:
                cost_text = "MAX"
            else:
                cost_text = f'${cost}'
            cost_surf = font.render(cost_text, True, (255, 215, 0))
            cost_rect = cost_surf.get_rect(center=(line_x, start_y + slider_height + 20))
            self.display_surface.blit(cost_surf, cost_rect)

            label_surf = font.render(label, True, (0,0,0))
            label_rect = label_surf.get_rect(center=(line_x, start_y + 25))
            self.display_surface.blit(label_surf, label_rect)

        info = font.render("Press 1/2/3 to upgrade, E to resume", True, (220,220,220))
        info_rect = info.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 60))
        self.display_surface.blit(info, info_rect)

    def buy_upgrade(self, name):
        max_level = 10
        if self.upgrades[name] < max_level and self.coins >= self.upgrade_costs[name]:
            self.coins -= self.upgrade_costs[name]
            self.upgrades[name] += 1
            self.upgrade_costs[name] += 3
            if name == 'speed':
                self.player.speed = 500 + self.upgrades['speed'] * 50
            if name == 'health':
                self.player.max_health = 100 + self.upgrades['health'] * 20
                self.player.health = self.player.max_health
            # For enemy_slow, apply in your enemy logic (see below)

    def run(self):
        font = pygame.font.SysFont(None, 40)
        while self.running:
            # dt
            dt = self.clock.tick() / 1000
            
            # event loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == self.enemy_event and not self.upgrade_menu:
                    # Pass enemy_slow value to Enemy
                    slow = self.upgrades['enemy_slow'] * 20
                    Enemy(
                        choice(self.spawn_positions),
                        choice(list(self.enemy_frames.values())),
                        (self.all_sprites, self.enemy_sprites),
                        self.player,
                        self.collision_sprites,
                        slow=slow
                    )
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_e:
                        self.upgrade_menu = not self.upgrade_menu
                    if self.upgrade_menu:
                        if event.key == pygame.K_1:
                            self.buy_upgrade('speed')
                        if event.key == pygame.K_2:
                            self.buy_upgrade('enemy_slow')
                        if event.key == pygame.K_3:
                            self.buy_upgrade('health')

            # update
            self.gun_timer()
            if not self.upgrade_menu:
                self.input()
                self.all_sprites.update(dt)
                self.bullet_collision()
                self.player_collision()

            # draw
            self.display_surface.fill('black')
            self.all_sprites.draw(self.player.rect.center)

            # Draw coin counter
            coin_surf = font.render(f'Coins: {self.coins}', True, (255, 255, 0))
            self.display_surface.blit(coin_surf, (20, 20))

            # Draw upgrade menu if open
            if self.upgrade_menu:
                self.draw_upgrade_menu(font)

            pygame.display.update()
        
        pygame.quit()

if __name__ == '__main__':
    game = Game()
    game.run()