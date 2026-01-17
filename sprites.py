# Sprites pour Leak To The Past

import pygame
from random import uniform, randint
from math import sin
from settings import TILESIZE, CYAN, RED, MAX_AMMO, ITEM_DESPAWN_TIME, WINDOW_WIDTH, WINDOW_HEIGHT


class Player(pygame.sprite.Sprite):
    
    def __init__(self, game, groups, pos):
        super().__init__(groups)
        self.game = game
        
        self.load_images()
        
        # Animation
        self.direction_name = 'south'
        self.frame_index = 0
        self.animation_speed = 12
        self.is_moving = False
        
        # Image par défaut (statique)
        self.image = self.static_images['south']
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-60, -60)
        
        self.pos = pygame.math.Vector2(pos)
        self.direction = pygame.math.Vector2(0, 0)
        self.speed = 500
        self.base_speed = 500  # Vitesse de base pour pouvoir ralentir
        
        # Munitions
        self.ammo = MAX_AMMO
        self.max_ammo = MAX_AMMO
        self.next_shot_special = False
    
    def load_images(self):
        # Charger le spritesheet
        spritesheet = pygame.image.load('assets/graphics/spritesheet/leak.png').convert_alpha()
        
        # Dimensions du spritesheet
        sheet_width = spritesheet.get_width()
        sheet_height = spritesheet.get_height()
        cols = 7  # 1 static + 6 anim
        rows = 8  # 8 directions
        cell_width = sheet_width // cols
        cell_height = sheet_height // rows
        
        # Ordre des directions dans le spritesheet (lignes)
        directions_order = [
            'south', 'south-west', 'west', 'north-west',
            'north', 'north-east', 'east', 'south-east'
        ]
        
        self.static_images = {}
        self.animations = {}
        
        for row, direction in enumerate(directions_order):
            # Colonne 0 = statique
            static_rect = pygame.Rect(0, row * cell_height, cell_width, cell_height)
            static_img = spritesheet.subsurface(static_rect).copy()
            self.static_images[direction] = pygame.transform.scale(static_img, (TILESIZE, TILESIZE))
            
            # Colonnes 1-6 = animation
            self.animations[direction] = []
            for col in range(1, cols):
                frame_rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)
                frame_img = spritesheet.subsurface(frame_rect).copy()
                self.animations[direction].append(pygame.transform.scale(frame_img, (TILESIZE, TILESIZE)))
    
    def get_direction_name(self):
        if self.direction.x == 0 and self.direction.y == 0:
            return
        
        # 8 directions
        if self.direction.y < 0 and abs(self.direction.x) < 0.4:
            self.direction_name = 'north'
        elif self.direction.y > 0 and abs(self.direction.x) < 0.4:
            self.direction_name = 'south'
        elif self.direction.x > 0 and abs(self.direction.y) < 0.4:
            self.direction_name = 'east'
        elif self.direction.x < 0 and abs(self.direction.y) < 0.4:
            self.direction_name = 'west'
        elif self.direction.y < 0 and self.direction.x > 0:
            self.direction_name = 'north-east'
        elif self.direction.y < 0 and self.direction.x < 0:
            self.direction_name = 'north-west'
        elif self.direction.y > 0 and self.direction.x > 0:
            self.direction_name = 'south-east'
        elif self.direction.y > 0 and self.direction.x < 0:
            self.direction_name = 'south-west'
    
    def animate(self, dt):
        if self.is_moving:
            self.frame_index += self.animation_speed * dt
            if self.frame_index >= len(self.animations[self.direction_name]):
                self.frame_index = 0
            self.image = self.animations[self.direction_name][int(self.frame_index)]
        else:
            self.image = self.static_images[self.direction_name]
            self.frame_index = 0
    
    def input(self):
        keys = pygame.key.get_pressed()
        
        self.direction.x = 0
        self.direction.y = 0
        
        if keys[pygame.K_z] or keys[pygame.K_w] or keys[pygame.K_UP]:
            self.direction.y = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.direction.y = 1
        
        if keys[pygame.K_q] or keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.direction.x = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.direction.x = 1
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
            self.is_moving = True
        else:
            self.is_moving = False
            
    def update(self, dt):
        self.input()
        self.get_direction_name()
        self.animate(dt)
        
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
        'blue': {'color': (50, 50, 255), 'speed': 180, 'health': 2},
        'red': {'color': (255, 50, 50), 'speed': 100, 'health': 10},
        'purple': {'color': (200, 50, 200), 'speed': 350, 'health': 2}
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
        
        # Taille selon le type
        self.size = 128 if monster_type == 'yellow' else 64
        
        self.load_images()
        
        # Animation
        self.direction_name = 'south'
        self.frame_index = 0
        self.animation_speed = self.speed / 25  # Adapté à la vitesse
        
        # Image par défaut (statique)
        self.image = self.static_images['south']
        
        self.rect = self.image.get_rect(center=pos)
        
        # Hitbox plus petite pour le purple (plus dur à toucher)
        if monster_type == 'purple':
            self.hitbox = self.rect.inflate(-50, -50)
        else:
            self.hitbox = self.rect.inflate(-40, -40)
        
        self.pos = pygame.math.Vector2(pos)
        
        # Timer TP pour le violet (très fréquent)
        self.tp_cooldown = 800 if monster_type == 'purple' else 3000
        self.last_tp = pygame.time.get_ticks()
        
        # Mouvement zigzag pour purple
        self.zigzag_timer = 0
        self.zigzag_offset = 1
        
        # Hit Flash
        self.last_hit_time = 0
        self.hit_duration = 100 # ms
        self.is_hit = False
        
        # Pour le bleu (Tir)
        self.shoot_cooldown = 2000  # 2 secondes
        self.last_shoot_time = pygame.time.get_ticks()
    
    def load_images(self):
        # Charger le spritesheet
        spritesheet = pygame.image.load('assets/graphics/spritesheet/snot.png').convert_alpha()
        
        # Dimensions du spritesheet
        sheet_width = spritesheet.get_width()
        sheet_height = spritesheet.get_height()
        cols = 7  # 1 static + 6 anim
        rows = 8  # 8 directions
        cell_width = sheet_width // cols
        cell_height = sheet_height // rows
        
        # Ordre des directions dans le spritesheet (lignes)
        directions_order = [
            'south', 'south-west', 'west', 'north-west',
            'north', 'north-east', 'east', 'south-east'
        ]
        
        self.static_images = {}
        self.animations = {}
        
        for row, direction in enumerate(directions_order):
            # Colonne 0 = statique
            static_rect = pygame.Rect(0, row * cell_height, cell_width, cell_height)
            static_img = spritesheet.subsurface(static_rect).copy()
            static_img = pygame.transform.scale(static_img, (self.size, self.size))
            if self.color:
                static_img.fill(self.color, special_flags=pygame.BLEND_MULT)
            self.static_images[direction] = static_img
            
            # Colonnes 1-6 = animation
            self.animations[direction] = []
            for col in range(1, cols):
                frame_rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)
                frame_img = spritesheet.subsurface(frame_rect).copy()
                frame_img = pygame.transform.scale(frame_img, (self.size, self.size))
                if self.color:
                    frame_img.fill(self.color, special_flags=pygame.BLEND_MULT)
                self.animations[direction].append(frame_img)
    
    def get_direction_name(self, direction):
        if direction.length() == 0:
            return
        
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
    
    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        if self.frame_index >= len(self.animations[self.direction_name]):
            self.frame_index = 0
        self.image = self.animations[self.direction_name][int(self.frame_index)]
    
    def move(self, dt):
        direction = self.player.pos - self.pos
        
        if direction.length() > 0:
            direction = direction.normalize()
        
        # Comportement spécifique : Blue (Reste à distance et tire)
        if self.monster_type == 'blue':
            dist_to_player = (self.player.pos - self.pos).length()
            desired_dist = 300
            
            # Si trop proche, recule
            if dist_to_player < desired_dist - 50:
                direction = -direction
            # Si à bonne distance, ne bouge pas (ou bouge peu)
            elif dist_to_player < desired_dist + 50:
                direction = pygame.math.Vector2(0, 0)
            
            # Tirer
            current_time = pygame.time.get_ticks()
            if current_time - self.last_shoot_time > self.shoot_cooldown:
                self.shoot_at_player()
                self.last_shoot_time = current_time
        
        # Zigzag pour le purple (plus dur à viser)
        if self.monster_type == 'purple':
            self.zigzag_timer += dt
            if self.zigzag_timer > 0.2:
                self.zigzag_timer = 0
                self.zigzag_offset *= -1
            
            # Perpendiculaire à la direction
            perp = pygame.math.Vector2(-direction.y, direction.x)
            direction = direction + perp * self.zigzag_offset * 0.5
            direction = direction.normalize()
        
        self.get_direction_name(direction)
        self.animate(dt)
        
        # Effet flash blanc si touché
        if self.is_hit:
            current = pygame.time.get_ticks()
            if current - self.last_hit_time < self.hit_duration:
                # Version blanche
                white_surf = self.image.copy()
                white_surf.fill((255, 255, 255, 255), special_flags=pygame.BLEND_ADD)
                self.image = white_surf
            else:
                self.is_hit = False
        
        # Camouflage du violet (quasi-invisible quand proche)
        if self.monster_type == 'purple':
            dist = (self.player.pos - self.pos).length()
            if dist < 300:
                # Proche = très faible opacité (presque invisible sur sol sombre)
                self.image.set_alpha(30)
            else:
                # Loin = visible en violet
                self.image.set_alpha(255)
        
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
                self.rect.center = (round(self.pos.x), round(self.pos.y))
                self.last_tp = now
    
    def shoot_at_player(self):
        # Position du joueur
        player_pos = self.player.rect.center
        enemy_pos = self.rect.center
        direction = pygame.math.Vector2(player_pos) - pygame.math.Vector2(enemy_pos)
        
        # Vérifie si le joueur est visible à l'écran
        dx = abs(player_pos[0] - enemy_pos[0])
        dy = abs(player_pos[1] - enemy_pos[1])
        
        # Si hors écran, ne tire pas
        if dx > WINDOW_WIDTH // 2 + 100 or dy > WINDOW_HEIGHT // 2 + 100:
            return
        
        if hasattr(self.game, 'enemy_bullets'):
            EnemyBullet(enemy_pos, direction, [self.game.all_sprites, self.game.enemy_bullets])
            # Son de tir
            if hasattr(self.game, 'blue_shoot_sounds'):
                from random import choice
                choice(self.game.blue_shoot_sounds).play()


class Bullet(pygame.sprite.Sprite):
    
    def __init__(self, pos, direction, groups, is_special=False):
        super().__init__(groups)
        
        self.is_special = is_special
        
        # Projectile: Barre cyan orientée (ou ROUGE si spécial)
        self.image = pygame.Surface((24, 6), pygame.SRCALPHA)
        if is_special:
            self.image.fill(RED)
        else:
            self.image.fill(CYAN)
        
        if direction.length() > 0:
            self.direction = direction.normalize()
        else:
            self.direction = pygame.math.Vector2(0, -1)
            
        # Rotation selon la direction
        angle = self.direction.angle_to(pygame.math.Vector2(1, 0))
        self.image = pygame.transform.rotate(self.image, angle)
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(pos)
        
        self.speed = 800
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


class Puddle(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        
        # Grande flaque verte semi-transparente
        size = randint(40, 60)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 255, 0, 100), (size//2, size//2), size//2)
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-10, -10)
        
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 5000  # 5 secondes
        
    def update(self, dt):
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, groups):
        super().__init__(groups)
        
        self.image = pygame.Surface((12, 12))
        self.image.fill((50, 50, 255))  # Bleu
        pygame.draw.circle(self.image, (200, 200, 255), (6, 6), 4)
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-4, -4)
        
        self.pos = pygame.math.Vector2(pos)
        if direction.length() > 0:
            self.direction = direction.normalize()
        else:
            self.direction = pygame.math.Vector2(1, 0)
            
        self.speed = 300
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 3000
    
    def update(self, dt):
        self.pos += self.direction * self.speed * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.hitbox.center = self.rect.center
        
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()


class Item(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        
        # Visuel : Fiole spray (Image réelle)
        self.image = pygame.image.load('assets/graphics/HUD/nasal_spray.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.type = 'nasal_spray'
        self.image = pygame.transform.rotate(self.image, -45)
        
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-30, -30)
        
        self.pos = pygame.math.Vector2(pos)
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = ITEM_DESPAWN_TIME
        
        self.y_start = self.pos.y
        self.float_timer = 0
        
    def update(self, dt):
        # Animation flottante
        self.float_timer += dt * 5
        self.pos.y = self.y_start + sin(self.float_timer) * 5
        self.rect.centery = round(self.pos.y)
        self.hitbox.center = self.rect.center
        
        # Clignotement fin de vie
        age = pygame.time.get_ticks() - self.spawn_time
        if age > self.lifetime - 2000:
            if (age // 200) % 2 == 0:
                self.image.set_alpha(100)
            else:
                self.image.set_alpha(255)
                
        if age > self.lifetime:
            self.kill()
