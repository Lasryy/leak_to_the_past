# Sprites pour Leak To The Past

import pygame
from settings import TILESIZE, CYAN


class Player(pygame.sprite.Sprite):
    
    def __init__(self, game, groups, pos):
        super().__init__(groups)
        self.game = game
        
        self.load_images()
        
        # Image par défaut
        self.image = self.images['south']
        self.direction_name = 'south'
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-20, -20)
        
        self.pos = pygame.math.Vector2(pos)
        self.direction = pygame.math.Vector2(0, 0)
        
        # Vitesse du joueur
        self.speed = 500
    
    def load_images(self):
        self.images = {}
        rotations_path = 'assets/graphics/leak/rotations/'
        
        directions = [
            'north', 'south', 'east', 'west',
            'north-east', 'north-west', 'south-east', 'south-west'
        ]
        
        for direction in directions:
            image = pygame.image.load(f'{rotations_path}{direction}.png').convert_alpha()
            self.images[direction] = pygame.transform.scale(image, (TILESIZE, TILESIZE))
    
    def update_image(self):
        if self.direction.x == 0 and self.direction.y == 0:
            return
        
        # 8 directions
        if self.direction.y < 0 and self.direction.x == 0:
            self.direction_name = 'north'
        elif self.direction.y > 0 and self.direction.x == 0:
            self.direction_name = 'south'
        elif self.direction.x > 0 and self.direction.y == 0:
            self.direction_name = 'east'
        elif self.direction.x < 0 and self.direction.y == 0:
            self.direction_name = 'west'
        elif self.direction.y < 0 and self.direction.x > 0:
            self.direction_name = 'north-east'
        elif self.direction.y < 0 and self.direction.x < 0:
            self.direction_name = 'north-west'
        elif self.direction.y > 0 and self.direction.x > 0:
            self.direction_name = 'south-east'
        elif self.direction.y > 0 and self.direction.x < 0:
            self.direction_name = 'south-west'
        
        self.image = self.images[self.direction_name]
    
    def input(self):
        keys = pygame.key.get_pressed()
        
        self.direction.x = 0
        self.direction.y = 0
        
        # Vertical
        if keys[pygame.K_z] or keys[pygame.K_UP]:
            self.direction.y = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.direction.y = 1
        
        # Horizontal
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            self.direction.x = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.direction.x = 1
        
        # Fix diagonale
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
    
    def update(self, dt):
        self.input()
        self.update_image()
        
        self.pos += self.direction * self.speed * dt
        
        self.rect.centerx = round(self.pos.x)
        self.rect.centery = round(self.pos.y)
        self.hitbox.center = self.rect.center


class Enemy(pygame.sprite.Sprite):
    
    def __init__(self, game, groups, pos, player):
        super().__init__(groups)
        self.game = game
        self.player = player
        
        self.load_images()
        
        # Image par défaut (vers le joueur = sud)
        self.image = self.images['south']
        self.direction_name = 'south'
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-10, -10)
        
        self.pos = pygame.math.Vector2(pos)
        self.speed = 150
    
    def load_images(self):
        self.images = {}
        rotations_path = 'assets/graphics/snot/rotations/'
        
        directions = [
            'north', 'south', 'east', 'west',
            'north-east', 'north-west', 'south-east', 'south-west'
        ]
        
        for direction in directions:
            image = pygame.image.load(f'{rotations_path}{direction}.png').convert_alpha()
            self.images[direction] = pygame.transform.scale(image, (64, 64))
    
    def update_image(self, direction):
        if direction.length() == 0:
            return
        
        # 8 directions
        if direction.y < 0 and abs(direction.x) < 0.4:
            self.direction_name = 'north'
        elif direction.y > 0 and abs(direction.x) < 0.4:
            self.direction_name = 'south'
        elif direction.x > 0 and abs(direction.y) < 0.4:
            self.direction_name = 'east'
        elif direction.x < 0 and abs(direction.y) < 0.4:
            self.direction_name = 'west'
        elif direction.y < 0 and direction.x > 0:
            self.direction_name = 'north-east'
        elif direction.y < 0 and direction.x < 0:
            self.direction_name = 'north-west'
        elif direction.y > 0 and direction.x > 0:
            self.direction_name = 'south-east'
        elif direction.y > 0 and direction.x < 0:
            self.direction_name = 'south-west'
        
        self.image = self.images[self.direction_name]
    
    def move(self, dt):
        # Vecteur vers le joueur
        direction = self.player.pos - self.pos
        
        if direction.length() > 0:
            direction = direction.normalize()
        
        self.update_image(direction)
        
        self.pos += direction * self.speed * dt
        
        self.rect.centerx = round(self.pos.x)
        self.rect.centery = round(self.pos.y)
        self.hitbox.center = self.rect.center
    
    def update(self, dt):
        self.move(dt)


class Bullet(pygame.sprite.Sprite):
    
    def __init__(self, pos, direction, groups):
        super().__init__(groups)
        
        # Projectile cyan néon
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(self.image, CYAN, (10, 10), 8)
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        
        if direction.length() > 0:
            self.direction = direction.normalize()
        else:
            self.direction = pygame.math.Vector2(0, -1)
        
        self.speed = 600
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 1000
    
    def update(self, dt):
        self.pos += self.direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # Disparaît après lifetime
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()
