# Sprites pour Leak To The Past

import pygame
from random import uniform
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
    
    # Config des types de monstres
    TYPES = {
        'normal': {'color': None, 'speed': 150, 'health': 1},
        'green': {'color': (100, 255, 100), 'speed': 250, 'health': 1},
        'yellow': {'color': (255, 255, 100), 'speed': 200, 'health': 2},
        'red': {'color': (255, 50, 50), 'speed': 100, 'health': 10},
        'purple': {'color': (200, 50, 200), 'speed': 300, 'health': 2}
    }
    
    def __init__(self, game, groups, pos, player, monster_type='normal'):
        super().__init__(groups)
        self.game = game
        self.player = player
        self.monster_type = monster_type
        self.groups_ref = groups
        
        # Stats selon le type
        config = self.TYPES[monster_type]
        self.speed = config['speed']
        self.health = config['health']
        self.color = config['color']
        
        self.load_images()
        
        # Image par défaut
        self.image = self.images['south']
        self.direction_name = 'south'
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-10, -10)
        
        self.pos = pygame.math.Vector2(pos)
        
        # Timer TP pour le violet
        self.tp_cooldown = 3000
        self.last_tp = pygame.time.get_ticks()
    
    def load_images(self):
        self.images = {}
        rotations_path = 'assets/graphics/snot/rotations/'
        
        directions = [
            'north', 'south', 'east', 'west',
            'north-east', 'north-west', 'south-east', 'south-west'
        ]
        
        # Taille selon le type
        size = 128 if self.monster_type == 'yellow' else 64
        
        for direction in directions:
            image = pygame.image.load(f'{rotations_path}{direction}.png').convert_alpha()
            image = pygame.transform.scale(image, (size, size))
            
            # Applique la couleur si définie
            if self.color:
                image.fill(self.color, special_flags=pygame.BLEND_MULT)
            
            self.images[direction] = image
    
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
        
        # TP du violet
        if self.monster_type == 'purple':
            self.try_teleport()
    
    def try_teleport(self):
        now = pygame.time.get_ticks()
        if now - self.last_tp < self.tp_cooldown:
            return
        
        # Trouve l'ennemi le plus proche du joueur (autre que soi)
        closest = None
        min_dist = float('inf')
        
        for sprite in self.game.enemies:
            if sprite is self:
                continue
            dist = (sprite.pos - self.player.pos).length()
            if dist < min_dist:
                min_dist = dist
                closest = sprite
        
        # TP derrière cet ennemi
        if closest:
            direction = (closest.pos - self.player.pos)
            if direction.length() > 0:
                direction = direction.normalize()
                self.pos = closest.pos + direction * 50
                self.rect.center = (round(self.pos.x), round(self.pos.y))
                self.last_tp = now


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


class Particle(pygame.sprite.Sprite):
    
    def __init__(self, pos, color, groups):
        super().__init__(groups)
        
        # Petit carré coloré
        self.image = pygame.Surface((4, 4))
        self.image.fill(color if color else (255, 255, 255))
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        
        # Direction aléatoire
        self.direction = pygame.math.Vector2(uniform(-1, 1), uniform(-1, 1))
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
        
        self.speed = uniform(100, 300)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = uniform(200, 500)
    
    def update(self, dt):
        self.pos += self.direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()

