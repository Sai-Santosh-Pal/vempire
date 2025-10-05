from settings import *
from math import atan2, degrees

class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)
        self.ground = True

class CollisionSprite(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft = pos)

class Gun(pygame.sprite.Sprite):
    def __init__(self, player, groups):
        # player connection
        self.player = player
        self.distance = 140
        self.player_direction = pygame.Vector2(0,1)

        # sprite setup
        super().__init__(groups)
        self.gun_surf = pygame.image.load(join('images', 'gun', 'gun.png'))
        self.image = self.gun_surf
        self.rect = self.image.get_rect(center = self.player.rect.center + self.player_direction * self.distance)

    def get_direction(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos()) 
        player_pos =  pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
        self.player_direction = (mouse_pos - player_pos).normalize()

    def rotate_gun(self):
        angle = degrees(atan2(self.player_direction.x, self.player_direction.y)) - 90
        if self.player_direction.x > 0:
            self.image = pygame.transform.rotozoom(self.gun_surf, angle, 1)
        else:
            self.image = pygame.transform.rotozoom(self.gun_surf, abs(angle), 1)
            self.image = pygame.transform.flip(self.image, False, True)
    
    def update(self, _):    
        self.get_direction()
        self.rotate_gun()
        self.rect.center = self.player.rect.center + self.player_direction * self.distance

class Bullet(pygame.sprite.Sprite):
    def __init__(self, surf, pos, direction, groups, speed=1200, power=1):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(center = pos)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1000

        self.direction = direction
        self.speed = speed
        self.power = power

    def update(self, dt):
        pos = pygame.Vector2(self.rect.center)
        pos += self.direction * self.speed * dt
        self.rect.center = (int(pos.x), int(pos.y))

        if pygame.time.get_ticks() - self.spawn_time >= self.lifetime:
            self.kill()

from settings import *
import pygame

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, frames, groups, player, collision_sprites, slow=0):
        super().__init__(groups)
        self.frames = frames
        self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-60, -90)

        self.player = player
        self.collision_sprites = collision_sprites

        # Movement
        base_speed = 350
        self.speed = max(base_speed - slow, 50)  # Apply enemy_slow, clamp to minimum
        self.direction = pygame.Vector2()

        # Animation
        self.death = False
        self.death_time = 0

    def animate(self, dt):
        if not self.death:
            self.frame_index += 5 * dt
            if self.frame_index >= len(self.frames):
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]
        else:
            # Optionally, play a death animation here
            pass

    def move(self, dt):
        # Move toward player
        player_pos = pygame.Vector2(self.player.rect.center)
        enemy_pos = pygame.Vector2(self.rect.center)
        direction_vector = player_pos - enemy_pos
        if direction_vector.length() != 0:
            self.direction = direction_vector.normalize()
        else:
            self.direction = pygame.Vector2()
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision("horizontal")
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision("vertical")
        self.rect.center = self.hitbox_rect.center

        # # get direction
        # player_pos = pygame.Vector2(self.player.rect.center)
        # enemy_pos = pygame.Vector2(self.rect.center)
        # self.direction = (player_pos - enemy_pos).normalize()

        # update the rect position + collision

    def collision(self, direction):
        for sprite in self.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if direction == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left = sprite.rect.right
                else:
                    if self.direction.y < 0: self.hitbox_rect.top = sprite.rect.bottom
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top

    def destroy(self):
        self.kill()

    def death_timer(self):
        if pygame.time.get_ticks() - self.death_time >= self.death_duration:
            self.kill()


    def update(self, dt):
        if not self.death:
            self.animate(dt)
            self.move(dt)