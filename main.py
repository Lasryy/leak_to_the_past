"""
Leak To The Past - Module Principal du Jeu
"""

import pygame
from pygame import mixer
from random import randint, random
from math import cos, sin, radians
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE, BLACK, WHITE, TILESIZE, MAX_AMMO, DROP_CHANCE
from sprites import Player, Enemy, Bullet, Particle, Puddle, Item


class CameraGroup(pygame.sprite.Group):
    
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        
        # Centre de l'écran
        self.half_width = self.display_surface.get_width() // 2
        self.half_height = self.display_surface.get_height() // 2
        
        # Décalage de la caméra
        self.offset = pygame.math.Vector2()
        
        # Création du sol dynamique
        self.floor_surf = pygame.Surface((TILESIZE, TILESIZE))
        self.floor_surf.fill((20, 20, 20))
        pygame.draw.rect(self.floor_surf, (40, 40, 40), self.floor_surf.get_rect(), width=1)
        
        # Fog of war avec alpha
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
        
        # Tuilage infini du sol
        start_col = int(self.offset.x // TILESIZE) - 1
        end_col = int((self.offset.x + WINDOW_WIDTH) // TILESIZE) + 1
        start_row = int(self.offset.y // TILESIZE) - 1
        end_row = int((self.offset.y + WINDOW_HEIGHT) // TILESIZE) + 1
        
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                x = col * TILESIZE - self.offset.x
                y = row * TILESIZE - self.offset.y
                self.display_surface.blit(self.floor_surf, (x, y))
        
        # Sépare les flaques et les autres sprites
        puddles = [s for s in self.sprites() if isinstance(s, Puddle)]
        others = [s for s in self.sprites() if not isinstance(s, Puddle)]
        
        # Dessine les flaques en premier (au sol)
        for sprite in puddles:
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)
            
        # Dessine les autres sprites triés par Y (Y-sort)
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
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
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
        
        # Timer pour spawn des ennemis
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 1000)
        
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 1000)
        
        # Etats du jeu
        self.state = 'menu' # menu, game, game_over
        self.game_over_timer = 0
        
        self.start_new_game()
    
    def start_new_game(self):
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
        self.sprays = 99  # Nombre de sprays (infini pour l'instant)
    
    def spawn_enemy(self):
        # Spawn en cercle autour du joueur
        distance = randint(1000, 1200)
        angle = randint(0, 360)
        
        x = self.player.rect.centerx + distance * cos(radians(angle))
        y = self.player.rect.centery + distance * sin(radians(angle))
        
        # Type aléatoire (60% normal, 15% green, 15% yellow, 7% blue, 2% red, 1% purple)
        roll = randint(1, 100)
        if roll <= 60:
            monster_type = 'normal'
        elif roll <= 75:
            monster_type = 'green'
        elif roll <= 90:
            monster_type = 'yellow'
        elif roll <= 97:
            monster_type = 'blue'
        elif roll <= 99:
            monster_type = 'red'
        else:
            monster_type = 'purple'
        
        Enemy(self, [self.all_sprites, self.enemies], (x, y), self.player, monster_type)
    
    def shoot(self, mouse_pos):
        # Vérifie les munitions
        if self.player.ammo <= 0:
            return
            
        self.player.ammo -= 1
        
        # Position du joueur à l'écran (toujours au centre)
        player_screen_pos = pygame.math.Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        mouse_vec = pygame.math.Vector2(mouse_pos)
        
        # Calcul de la direction
        direction = mouse_vec - player_screen_pos
        
        # Fait regarder le joueur vers la souris
        if direction.length() > 0:
            norm_dir = direction.normalize()
            
            # Détermine la direction (8 directions)
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
            [self.all_sprites, self.bullets]
        )
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == self.enemy_event:
                self.spawn_enemy()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Peut tirer seulement si immobile
                if not self.player.is_moving:
                    self.shoot(event.pos)
    
    def check_bullet_collisions(self):
        # Collisions balles/ennemis avec gestion de la vie
        hits = pygame.sprite.groupcollide(self.bullets, self.enemies, True, False)
        
        for bullet, enemies_hit in hits.items():
            for enemy in enemies_hit:
                enemy.health -= 1
                enemy.is_hit = True
                enemy.last_hit_time = pygame.time.get_ticks()
                
                if enemy.health <= 0:
                    # Particules d'explosion
                    for _ in range(8):
                        Particle(enemy.pos, enemy.color, self.all_sprites)
                    
                    # Score selon le type
                    self.score += self.SCORE_VALUES.get(enemy.monster_type, 10)
                    
                    # Rouge donne un cœur (max 3)
                    if enemy.monster_type == 'red' and self.hearts < 3:
                        self.hearts += 1
                    
                    # Le jaune spawn 2 verts en mourant
                    if enemy.monster_type == 'yellow':
                        for _ in range(2):
                            offset = pygame.math.Vector2(randint(-50, 50), randint(-50, 50))
                            Enemy(self, [self.all_sprites, self.enemies], 
                                  enemy.pos + offset, self.player, 'green')
                    
                    # Les verts et jaunes laissent une flaque
                    if enemy.monster_type in ['green', 'yellow']:
                        Puddle(enemy.pos, [self.all_sprites, self.puddles])
                        
                    # Drop d'item (munitions)
                    # Toujours pour le bleu, sinon chance globale
                    if enemy.monster_type == 'blue' or random() < DROP_CHANCE:
                        Item(enemy.pos, [self.all_sprites, self.items])
                    
                    enemy.kill()
    
    def update(self, dt):
        self.all_sprites.update(dt)
        self.check_bullet_collisions()
        
        # Mort du joueur (collision hitbox)
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

        # Gestion des flaques de morve (Ralentissement avec hitbox)
        is_slowed = False
        for puddle in self.puddles:
            if self.player.hitbox.colliderect(puddle.hitbox):
                is_slowed = True
                break
        
        if is_slowed:
            self.player.speed = self.player.base_speed / 2
        else:
            self.player.speed = self.player.base_speed
        
        # Collision balles ennemies / Joueur
        if pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_mask):
            self.hearts -= 1
            if self.hearts <= 0:
                self.state = 'game_over'
                self.game_over_timer = pygame.time.get_ticks()
        
        # Pickup items (Munitions)
        hit_item = pygame.sprite.spritecollideany(self.player, self.items)
        if hit_item:
            hit_item.kill()
            self.player.ammo = MAX_AMMO

    def update_menu(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.start_new_game()
            self.state = 'game'
            
    def update_game_over(self):
        if pygame.time.get_ticks() - self.game_over_timer > 3000:
            self.state = 'menu'

    def draw_menu(self):
        self.screen.fill(BLACK)
        title_surf = self.font.render(TITLE, True, (0, 255, 255)) # Cyan title
        text_surf = self.font.render("PRESS SPACE TO START", True, WHITE)
        
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        text_rect = text_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        
        self.screen.blit(title_surf, title_rect)
        self.screen.blit(text_surf, text_rect)
        pygame.display.flip()

    def draw_game_over(self):
        self.screen.fill(BLACK)
        title_surf = self.font.render("GAME OVER", True, (255, 0, 0))
        score_surf = self.font.render(f"Score: {self.score}", True, WHITE)
        
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        score_rect = score_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        
        self.screen.blit(title_surf, title_rect)
        self.screen.blit(score_surf, score_rect)
        pygame.display.flip()
    
    def draw_ui(self):
        # === HOTBAR EN BAS (style Minecraft - 9 slots) ===
        slot_size = 50
        slot_margin = 3
        num_slots = 9
        hotbar_width = num_slots * (slot_size + slot_margin) + slot_margin
        hotbar_height = slot_size + slot_margin * 2
        hotbar_x = WINDOW_WIDTH // 2 - hotbar_width // 2
        hotbar_y = WINDOW_HEIGHT - hotbar_height - 10
        
        # Fond du hotbar
        pygame.draw.rect(self.screen, (50, 50, 50), (hotbar_x, hotbar_y, hotbar_width, hotbar_height))
        pygame.draw.rect(self.screen, (30, 30, 30), (hotbar_x, hotbar_y, hotbar_width, hotbar_height), 2)
        
        # Dessine les 9 slots
        for i in range(num_slots):
            sx = hotbar_x + slot_margin + i * (slot_size + slot_margin)
            sy = hotbar_y + slot_margin
            
            # Fond du slot
            pygame.draw.rect(self.screen, (80, 80, 80), (sx, sy, slot_size, slot_size))
            
            # Bordure (blanche si sélectionné, grise sinon)
            if i == 0:
                pygame.draw.rect(self.screen, (255, 255, 255), (sx, sy, slot_size, slot_size), 2)
                # Spray nasal dans le premier slot
                spray_rect = self.spray_icon.get_rect(center=(sx + slot_size // 2, sy + slot_size // 2))
                self.screen.blit(self.spray_icon, spray_rect)
                
                # Barre de durabilité dans le slot (si utilisé)
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
                    
            else:
                pygame.draw.rect(self.screen, (40, 40, 40), (sx, sy, slot_size, slot_size), 1)
        
        # === CŒURS AU-DESSUS DU HOTBAR (à gauche) ===
        heart_y = hotbar_y - 28
        for i in range(self.hearts):
            heart_rect = self.heart_icon.get_rect(center=(hotbar_x + 15 + i * 28, heart_y))
            self.screen.blit(self.heart_icon, heart_rect)
        
        # === NOM DE L'ITEM AU CENTRE AU-DESSUS DU HOTBAR ===
        item_name = "Nasal Spray"
        name_shadow = self.hotbar_font.render(item_name, True, (0, 0, 0))
        name_surf = self.hotbar_font.render(item_name, True, (255, 255, 255))
        name_x = WINDOW_WIDTH // 2 - name_surf.get_width() // 2
        name_y = hotbar_y - 25
        self.screen.blit(name_shadow, (name_x + 1, name_y + 1))
        self.screen.blit(name_surf, (name_x, name_y))
        
        # === SCORE EN HAUT A DROITE ===
        score_text = f'Score: {self.score}'
        shadow = self.hotbar_font.render(score_text, True, (0, 0, 0))
        self.screen.blit(shadow, (WINDOW_WIDTH - 151, 21))
        score_surf = self.hotbar_font.render(score_text, True, (255, 255, 255))
        self.screen.blit(score_surf, (WINDOW_WIDTH - 150, 20))
    
    def draw(self):
        self.screen.fill(BLACK)
        self.all_sprites.custom_draw(self.player)
        self.draw_ui()
        pygame.display.flip()
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            
            self.handle_events()
            
            if self.state == 'menu':
                self.update_menu()
                self.draw_menu()
            elif self.state == 'game':
                self.update(dt)
                self.draw()
            elif self.state == 'game_over':
                self.update_game_over()
                self.draw_game_over()
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
