"""
Leak To The Past - Module Principal du Jeu
"""

import asyncio
import pygame
from pygame import mixer
from random import randint, random, choices, choice, shuffle
from math import cos, sin, radians
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE, BLACK, WHITE, TILESIZE, MAX_AMMO, DROP_CHANCE, MASTER_VOLUME, MUSIC_VOLUME, SFX_VOLUME
from sprites import Player, Enemy, Bullet, Particle, Puddle, Item


class CameraGroup(pygame.sprite.Group):
    
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        
        # Centre de l'écran
        self.half_width = self.display_surface.get_width() // 2
        self.half_height = self.display_surface.get_height() // 2
        
        self.offset = pygame.math.Vector2()
        
        self.floor_surf = pygame.Surface((TILESIZE, TILESIZE))
        self.floor_surf.fill((20, 20, 20))
        pygame.draw.rect(self.floor_surf, (40, 40, 40), self.floor_surf.get_rect(), width=1)
        
        # Fog
        self.fog_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        
        # Génère la texture de lumière
        self.light_mask = self.generate_flashlight(450)
        self.light_rect = self.light_mask.get_rect()
    
    @staticmethod
    def generate_flashlight(radius):
        size = radius * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        for r in range(radius, 0, -1):
            alpha = int(255 * (1 - r / radius))
            pygame.draw.circle(surf, (0, 0, 0, alpha), (radius, radius), r)
        
        return surf
    
    def custom_draw(self, player):
        # Calcul de l'offset
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height
        
        start_col = int(self.offset.x // TILESIZE) - 1
        end_col = int((self.offset.x + WINDOW_WIDTH) // TILESIZE) + 1
        start_row = int(self.offset.y // TILESIZE) - 1
        end_row = int((self.offset.y + WINDOW_HEIGHT) // TILESIZE) + 1
        
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                x = col * TILESIZE - self.offset.x
                y = row * TILESIZE - self.offset.y
                self.display_surface.blit(self.floor_surf, (x, y))
        
        puddles = [s for s in self.sprites() if isinstance(s, Puddle)]
        others = [s for s in self.sprites() if not isinstance(s, Puddle)]
        
        for sprite in puddles:
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)
            
        for sprite in sorted(others, key=lambda s: s.rect.centery):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)
            
        self.fog_surf.fill((20, 20, 35, 250))
        
        # Position de la lumière au centre de l'écran
        self.light_rect.center = (self.half_width, self.half_height)
        
        self.fog_surf.blit(self.light_mask, self.light_rect, special_flags=pygame.BLEND_RGBA_SUB)
        
        # Dessine le fog
        self.display_surface.blit(self.fog_surf, (0, 0))


class Game:
    
    # Points par type de monstre
    SCORE_VALUES = {
        'normal': 10,
        'green': 15,
        'yellow': 25,
        'red': 50,
        'purple': 100
    }
    
    def __init__(self):
        pygame.init()
        mixer.init()
        mixer.set_num_channels(32) 
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Volume (modifiable en jeu)
        self.master_volume = MASTER_VOLUME
        self.volume_display_timer = 0
        
        # Police pour le HUD
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 24)
        try:
            self.hotbar_font = pygame.font.Font('assets/font/Monocraft.ttf', 18)
        except FileNotFoundError:
            self.hotbar_font = pygame.font.Font(None, 18)
            print("Warning: Monocraft.ttf not found, using default font.")
        
        # Charge l'image du spray nasal 
        spray_img = pygame.image.load('assets/graphics/HUD/nasal_spray.png').convert_alpha()
        spray_img = pygame.transform.scale(spray_img, (40, 40))
        self.spray_icon = pygame.transform.rotate(spray_img, -45)
        
        # Charge l'image du coeur
        heart_img = pygame.image.load('assets/graphics/HUD/heart.png').convert_alpha()
        self.heart_icon = pygame.transform.scale(heart_img, (24, 24))
        
        # Optimisation rendu UI
        self.ui_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.ui_surface_dirty = True

        # Charge les sons (3 variations chacun)
        audio_path = 'assets/audio/'
        self.shoot_sounds = [
            mixer.Sound(f'{audio_path}nasal_spray.ogg'),
            mixer.Sound(f'{audio_path}nasal_spray 2.ogg'),
            mixer.Sound(f'{audio_path}nasal_spray 3.ogg')
        ]
        self.empty_sounds = [
            mixer.Sound(f'{audio_path}nasal_spray empty.ogg'),
            mixer.Sound(f'{audio_path}nasal_spray empty 2.ogg'),
            mixer.Sound(f'{audio_path}nasal_spray empty 3.ogg')
        ]
        self.blue_shoot_sounds = [
            mixer.Sound(f'{audio_path}blue shoot.ogg'),
            mixer.Sound(f'{audio_path}blue shoot 2.ogg'),
            mixer.Sound(f'{audio_path}blue shoot 3.ogg')
        ]
        self.recharge_sounds = [
            mixer.Sound(f'{audio_path}recharge.ogg'),
            mixer.Sound(f'{audio_path}recharge 2.ogg'),
            mixer.Sound(f'{audio_path}recharge 3.ogg')
        ]
        self.spawn_sounds = [
            mixer.Sound(f'{audio_path}snot spawn.ogg'),
            mixer.Sound(f'{audio_path}snot spawn 2.ogg'),
            mixer.Sound(f'{audio_path}snot spawn 3.ogg')
        ]
        self.blood_shoot_sounds = [
            mixer.Sound(f'{audio_path}blood_shoot.ogg'),
            mixer.Sound(f'{audio_path}blood_shoot 2.ogg'),
            mixer.Sound(f'{audio_path}blood_shoot 3.ogg'),
            mixer.Sound(f'{audio_path}blood_shoot 4.ogg')
        ]
        self.puddle_sounds = [
            mixer.Sound(f'{audio_path}flaque.ogg'),
            mixer.Sound(f'{audio_path}flaque 2.ogg'),
            mixer.Sound(f'{audio_path}flaque 3.ogg')
        ]
        
        # Applique le volume aux effets sonores
        all_sfx = (self.shoot_sounds + self.empty_sounds + self.blue_shoot_sounds + 
                   self.recharge_sounds + self.spawn_sounds + self.blood_shoot_sounds + 
                   self.puddle_sounds)
        for sound in all_sfx:
            sound.set_volume(SFX_VOLUME * MASTER_VOLUME)
        
        # Channel dédié pour le son "empty"
        self.empty_channel = mixer.Channel(0)
        self.puddle_channel = mixer.Channel(1)
        self.shoot_channel = mixer.Channel(2)
        
        # Timer pour spawn des ennemis
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 1000)
        
        # Etats du jeu
        self.state = 'menu' # menu, game, game_over
        self.game_over_timer = 0
        
        self.last_score = -1
        self.score_surf = None
        self.score_shadow = None

        item_text = "Nasal Spray"
        self.item_name_shadow = self.hotbar_font.render(item_text, True, (0, 0, 0))
        self.item_name_surf = self.hotbar_font.render(item_text, True, (255, 255, 255))
        
        # Playlist
        self.playlist = [
            'track_1.ogg',
            'track_2.ogg',
            'track_3.ogg',
            'track_4.ogg',
            'track_5.ogg',
            'track_6.ogg'
        ]
        shuffle(self.playlist)
        self.current_track = 0
        
        
        # Lance la première musique
        self.last_music_change = pygame.time.get_ticks()
        self.has_interaction = False
        
        # Timer pour l'astuce du volume
        self.hint_timer = 0
        
        self.start_new_game()
    
    def play_music(self):
        # Charge et joue la musique actuelle
        track_name = self.playlist[self.current_track]
        pygame.mixer.music.load(f'assets/audio/{track_name}')
        pygame.mixer.music.set_volume(MUSIC_VOLUME * MASTER_VOLUME)
        pygame.mixer.music.play()

    def start_new_game(self):
        if not hasattr(self, 'current_track'):
            self.current_track = 0
        
        # Groupes de sprites
        self.all_sprites = CameraGroup()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.puddles = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.items = pygame.sprite.Group()
        
        self.player = Player(
            self,
            self.all_sprites,
            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        )
        
        # Score et vie
        self.score = 0
        self.hearts = 1  # 1 cœur au départ, max 3
        self.sprays = 99 
        
        self.game_start_time = pygame.time.get_ticks()
    
    def spawn_enemy(self):
        # Spawn en cercle autour du joueur
        distance = randint(1000, 1200)
        angle = randint(0, 360)
        
        x = self.player.rect.centerx + distance * cos(radians(angle))
        y = self.player.rect.centery + distance * sin(radians(angle))
        
        # Types possibles selon le TEMPS DE JEU
        elapsed_time = (pygame.time.get_ticks() - self.game_start_time) / 1000
        
        potential_spawns = [
            {'type': 'normal', 'weight': 60, 'min_time': 0},
            {'type': 'green', 'weight': 15, 'min_time': 30},
            {'type': 'yellow', 'weight': 15, 'min_time': 60},
            {'type': 'blue', 'weight': 5, 'min_time': 90},
            {'type': 'red', 'weight': 2, 'min_time': 90},
            {'type': 'purple', 'weight': 1, 'min_time': 120}
        ]
        
        # Filtre les ennemis débloqués
        available = [s for s in potential_spawns if elapsed_time >= s['min_time']]
        
        if not available:
            monster_type = 'normal'
        else:
            # Choix parmi les disponibles
            types = [s['type'] for s in available]
            weights = [s['weight'] for s in available]
            monster_type = choices(types, weights=weights, k=1)[0]
        
        Enemy(self, [self.all_sprites, self.enemies], (x, y), self.player, monster_type)
        
        # Son de spawn uniquement pour le bleu
        if monster_type == 'blue':
            choice(self.spawn_sounds).play()
    
    def shoot(self, mouse_pos):

        is_special_shot = False
        if self.player.next_shot_special:
            is_special_shot = True
            self.player.next_shot_special = False
        
        # Vérifie les munitions
        if self.player.ammo <= 0:
            # BLOOD AMMO MECHANIC
            # Recharge au prix de la vie si : HP > 1 ET Pas de spray au sol
            
            has_spray_on_ground = False
            for item in self.items:
                if item.type == 'nasal_spray':
                    has_spray_on_ground = True
                    break
            
            if self.hearts > 1 and not has_spray_on_ground:
                # Sacrifice 1 HP
                self.hearts -= 1
                self.player.ammo = MAX_AMMO
                self.player.next_shot_special = True
                
                # Son de recharge
                choice(self.recharge_sounds).play()
                
                return
            else:
                # Pas de recharge possible -> Clic à vide
                if not self.empty_channel.get_busy():
                    self.empty_channel.play(choice(self.empty_sounds))
                return
        
        self.player.ammo -= 1
        
        # Son de tir
        self.shoot_channel.stop()
        self.shoot_channel.play(choice(self.shoot_sounds))
        
        # + Son BLOOD SHOOT
        if is_special_shot:
            choice(self.blood_shoot_sounds).play()
        
        # Position du joueur
        player_screen_pos = pygame.math.Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        mouse_vec = pygame.math.Vector2(mouse_pos)
        
        direction = mouse_vec - player_screen_pos
        
        # Fait regarder le joueur vers la souris
        if direction.length_squared() > 0:
            norm_dir = direction.normalize()
            
            # Détermine la direction 
            if norm_dir.y < -0.4 and abs(norm_dir.x) < 0.4:
                self.player.direction_name = 'north'
            elif norm_dir.y > 0.4 and abs(norm_dir.x) < 0.4:
                self.player.direction_name = 'south'
            elif norm_dir.x > 0.4 and abs(norm_dir.y) < 0.4:
                self.player.direction_name = 'east'
            elif norm_dir.x < -0.4 and abs(norm_dir.y) < 0.4:
                self.player.direction_name = 'west'
            elif norm_dir.y < 0 and norm_dir.x > 0:
                self.player.direction_name = 'north-east'
            elif norm_dir.y < 0 and norm_dir.x < 0:
                self.player.direction_name = 'north-west'
            elif norm_dir.y > 0 and norm_dir.x > 0:
                self.player.direction_name = 'south-east'
            elif norm_dir.y > 0 and norm_dir.x < 0:
                self.player.direction_name = 'south-west'
            
            self.player.image = self.player.static_images[self.player.direction_name]
        
        # Crée la balle
        Bullet(
            self.player.rect.center,
            direction,
            [self.all_sprites, self.bullets],
            is_special=is_special_shot
        )
    
    def handle_events(self):
        for event in pygame.event.get():
            # Gestion du premier input pour lancer l'audio
            if not self.has_interaction and (event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN):
                self.has_interaction = True
                self.hint_timer = pygame.time.get_ticks()  # Démarre le timer de l'astuce
                self.play_music()
                
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == self.enemy_event and self.state == 'game':
                self.spawn_enemy()
            
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Peut tirer seulement en jeu, si immobile
                if self.state == 'game' and not self.player.is_moving:
                    self.shoot(event.pos)
            
            # Contrôle du volume avec +/-
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    self.adjust_volume(0.1)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.adjust_volume(-0.1)
    
    def adjust_volume(self, delta):
        """Ajuste le volume principal"""
        self.master_volume = max(0.0, min(1.0, self.master_volume + delta))
        # Applique aux effets sonores
        all_sfx = (self.shoot_sounds + self.empty_sounds + self.blue_shoot_sounds + 
                   self.recharge_sounds + self.spawn_sounds + self.blood_shoot_sounds + 
                   self.puddle_sounds)
        for sound in all_sfx:
            sound.set_volume(SFX_VOLUME * self.master_volume)
        # Applique à la musique
        pygame.mixer.music.set_volume(MUSIC_VOLUME * self.master_volume)
        # Affiche le volume temporairement
        self.volume_display_timer = pygame.time.get_ticks()
    
    def check_bullet_collisions(self):
        # Collisions balles/ennemis avec gestion de la vie
        hits = pygame.sprite.groupcollide(self.bullets, self.enemies, True, False)
        
        for bullet, enemies_hit in hits.items():
            # Capture si c'est un tir spécial
            is_special_kill = getattr(bullet, 'is_special', False)
            
            for enemy in enemies_hit:
                # Gestion One-Shot
                if is_special_kill:
                    enemy.health = 0
                else:
                    enemy.health -= 1
                
                enemy.is_hit = True
                enemy.last_hit_time = pygame.time.get_ticks()
                
                if enemy.health <= 0:
                    # Particules d'explosion
                    for _ in range(8):
                        Particle(enemy.pos, enemy.color, self.all_sprites)
                    
                    # Score selon le type
                    self.score += self.SCORE_VALUES.get(enemy.monster_type, 10)
                    
                    # Rouge donne un cœur
                    if enemy.monster_type == 'red' and self.hearts < 3:
                        self.hearts += 1
                    
                    # Le jaune spawn 2 verts en mourant (SAUF si tué par blood bullet)
                    if enemy.monster_type == 'yellow' and not is_special_kill:
                        for _ in range(2):
                            offset = pygame.math.Vector2(randint(-50, 50), randint(-50, 50))
                            Enemy(self, [self.all_sprites, self.enemies], 
                                  enemy.pos + offset, self.player, 'green')
                    
                    if enemy.monster_type in ['green', 'yellow']:
                        Puddle(enemy.pos, [self.all_sprites, self.puddles])
                        
                    # Drop d'item
                    # Toujours pour le bleu
                    # Sinon, chance ajustée
                    if enemy.monster_type == 'blue':
                        Item(enemy.pos, [self.all_sprites, self.items])
                    else:
                        current_chance = DROP_CHANCE
                        if len(self.items) > 0:
                            current_chance = DROP_CHANCE / 5  # Réduit fortement si item au sol
                            
                        if random() < current_chance:
                            Item(enemy.pos, [self.all_sprites, self.items])
                    
                    enemy.kill()

    def manage_music(self):
        # Vérifie si la musique est terminée pour passer à la suivante
        if self.has_interaction and not pygame.mixer.music.get_busy():
            self.current_track = (self.current_track + 1) % len(self.playlist)
            self.play_music()
    
    def update(self, dt):
        self.all_sprites.update(dt)
        self.check_bullet_collisions()
        
        # Mort du joueur
        for enemy in self.enemies:
            if self.player.hitbox.colliderect(enemy.hitbox):
                self.hearts -= 1
                if self.hearts <= 0:
                    self.state = 'game_over'
                    self.game_over_timer = pygame.time.get_ticks()
                else:
                    # Juste tuer l'ennemi qui a touché
                    enemy.kill()
                break

        # Gestion des flaques de morve
        is_slowed = False
        for puddle in self.puddles:
            if self.player.hitbox.colliderect(puddle.hitbox):
                is_slowed = True
                break
        
        if is_slowed:
            self.player.speed = self.player.base_speed / 2
            # Joue le son de flaque (non-empilable)
            if not self.puddle_channel.get_busy():
                self.puddle_channel.play(choice(self.puddle_sounds))
        else:
            self.player.speed = self.player.base_speed
            # Arrête le son de flaque si on sort
            if self.puddle_channel.get_busy():
                self.puddle_channel.stop()
        
        # Collision balles ennemies / Joueur
        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_mask):
            self.hearts -= 1
            if self.hearts <= 0:
                self.state = 'game_over'
                self.game_over_timer = pygame.time.get_ticks()
        
        # Pickup items 
        for item in self.items:
            if self.player.hitbox.colliderect(item.hitbox):
                item.kill()
                self.player.ammo = MAX_AMMO
                choice(self.recharge_sounds).play()

    def update_menu(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.start_new_game()
            self.state = 'game'
            
    def update_game_over(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.start_new_game()
            self.state = 'game'

    def draw_menu(self):
        # Charger et afficher l'image de titre
        try:
            title_screen = pygame.image.load('assets/graphics/HUD/title_screen.png').convert()
            title_screen = pygame.transform.scale(title_screen, (WINDOW_WIDTH, WINDOW_HEIGHT))
            self.screen.blit(title_screen, (0, 0))
        except:
            self.screen.fill(BLACK)
            title_surf = self.font.render(TITLE, True, (0, 255, 255))
            text_surf = self.font.render("PRESS SPACE TO START", True, WHITE)
            title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            text_rect = text_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
            self.screen.blit(title_surf, title_rect)
            self.screen.blit(text_surf, text_rect)
        pygame.display.flip()

    def draw_game_over(self):
        # Afficher l'image de game over
        try:
            game_over_screen = pygame.image.load('assets/graphics/HUD/game_over_screen.png').convert()
            game_over_screen = pygame.transform.scale(game_over_screen, (WINDOW_WIDTH, WINDOW_HEIGHT))
            self.screen.blit(game_over_screen, (0, 0))
        except:
            self.screen.fill(BLACK)
            title_surf = self.font.render("GAME OVER", True, (255, 0, 0))
            score_surf = self.font.render(f"Score: {self.score}", True, WHITE)
            title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            score_rect = score_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
            self.screen.blit(title_surf, title_rect)
            self.screen.blit(score_surf, score_rect)
        
        # Afficher le score en haut à droite
        score_text = f'Score: {self.score}'
        score_shadow = self.hotbar_font.render(score_text, True, (0, 0, 0))
        score_surf = self.hotbar_font.render(score_text, True, WHITE)
        self.screen.blit(score_shadow, (WINDOW_WIDTH - 151, 21))
        self.screen.blit(score_surf, (WINDOW_WIDTH - 150, 20))
        
        pygame.display.flip()
    
    def draw_ui(self):
        # Hotbar style Minecraft
        slot_size = 50
        slot_margin = 3
        num_slots = 9
        hotbar_width = num_slots * (slot_size + slot_margin) + slot_margin
        hotbar_height = slot_size + slot_margin * 2
        hotbar_x = WINDOW_WIDTH // 2 - hotbar_width // 2
        hotbar_y = WINDOW_HEIGHT - hotbar_height - 10
        
        if self.ui_surface_dirty:
            self.ui_surface.fill((0,0,0,0))
            
            # Fond du hotbar
            pygame.draw.rect(self.ui_surface, (50, 50, 50), (hotbar_x, hotbar_y, hotbar_width, hotbar_height))
            pygame.draw.rect(self.ui_surface, (30, 30, 30), (hotbar_x, hotbar_y, hotbar_width, hotbar_height), 2)
            
            for i in range(num_slots):
                sx = hotbar_x + slot_margin + i * (slot_size + slot_margin)
                sy = hotbar_y + slot_margin
                
                pygame.draw.rect(self.ui_surface, (80, 80, 80), (sx, sy, slot_size, slot_size))
                
                if i != 0:
                    pygame.draw.rect(self.ui_surface, (40, 40, 40), (sx, sy, slot_size, slot_size), 1)
            
            self.ui_surface_dirty = False
            
        self.screen.blit(self.ui_surface, (0, 0))
        
        sx = hotbar_x + slot_margin # Slot 0
        sy = hotbar_y + slot_margin
        
        pygame.draw.rect(self.screen, (255, 255, 255), (sx, sy, slot_size, slot_size), 2)
        
        # Spray nasal dans le premier slot
        spray_rect = self.spray_icon.get_rect(center=(sx + slot_size // 2, sy + slot_size // 2))
        self.screen.blit(self.spray_icon, spray_rect)
        
        # Barre de durabilité
        if self.player.ammo < self.player.max_ammo:
            ratio = self.player.ammo / self.player.max_ammo
            bar_w = slot_size - 6
            bar_h = 4
            bar_x = sx + 3
            bar_y = sy + slot_size - 8
            
            # Couleur
            if ratio > 0.5:
                color = (0, 255, 0) # Vert
            elif ratio > 0.2:
                color = (255, 165, 0) # Orange
            else:
                color = (255, 0, 0) # Rouge
            
            # Fond noir
            pygame.draw.rect(self.screen, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            # Barre
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, bar_w * ratio, bar_h))
        
        # Coeur Hotbar
        heart_y = hotbar_y - 28
        for i in range(self.hearts):
            heart_rect = self.heart_icon.get_rect(center=(hotbar_x + 15 + i * 28, heart_y))
            self.screen.blit(self.heart_icon, heart_rect)
        
        # Nom de l'item
        name_x = WINDOW_WIDTH // 2 - self.item_name_surf.get_width() // 2
        name_y = hotbar_y - 25
        self.screen.blit(self.item_name_shadow, (name_x + 1, name_y + 1))
        self.screen.blit(self.item_name_surf, (name_x, name_y))
        
        if self.score != self.last_score or self.score_surf is None:
            score_text = f'Score: {self.score}'
            self.score_shadow = self.hotbar_font.render(score_text, True, (0, 0, 0))
            self.score_surf = self.hotbar_font.render(score_text, True, (255, 255, 255))
            self.last_score = self.score
            
        self.screen.blit(self.score_shadow, (WINDOW_WIDTH - 151, 21))
        self.screen.blit(self.score_surf, (WINDOW_WIDTH - 150, 20))
        
        # Affiche le volume temporairement (2 secondes)
        if pygame.time.get_ticks() - self.volume_display_timer < 2000:
            vol_pct = int(self.master_volume * 100)
            vol_text = f'Volume: {vol_pct}%'
            vol_shadow = self.hotbar_font.render(vol_text, True, (0, 0, 0))
            vol_surf = self.hotbar_font.render(vol_text, True, (255, 255, 255))
            self.screen.blit(vol_shadow, (21, 21))
            self.screen.blit(vol_surf, (20, 20))
        # Affiche l'astuce du volume pendant 5 secondes au démarrage
        elif self.hint_timer > 0 and pygame.time.get_ticks() - self.hint_timer < 5000:
            hint_text = "Régler le volume avec + et -"
            hint_shadow = self.hotbar_font.render(hint_text, True, (0, 0, 0))
            hint_surf = self.hotbar_font.render(hint_text, True, (200, 200, 200))
            self.screen.blit(hint_shadow, (21, 21))
            self.screen.blit(hint_surf, (20, 20))
    
    def draw(self):
        self.screen.fill(BLACK)
        self.all_sprites.custom_draw(self.player)
        self.draw_ui()
        pygame.display.flip()
    
    async def run(self):
        while True:
            if not self.running:
                break
                
            dt = self.clock.tick(FPS) / 1000
            dt = min(dt, 0.1)
            
            self.handle_events()
            self.manage_music()
            
            if self.state == 'menu':
                self.update_menu()
                self.draw_menu()
            elif self.state == 'game':
                self.update(dt)
                self.draw()
            elif self.state == 'game_over':
                self.update_game_over()
                self.draw_game_over()
            
            await asyncio.sleep(0)  # Pygbag
        
        pygame.quit()


async def main():
    game = Game()
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())
