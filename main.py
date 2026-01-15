"""
Leak To The Past - Module Principal du Jeu
"""

import pygame
from pygame import mixer
from random import randint
from math import cos, sin, radians
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE, BLACK, TILESIZE
from sprites import Player, Enemy


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
        
        # Dessine les sprites
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)
        
        self.fog_surf.fill((20, 20, 35, 250))
        
        # Position de la lumière au centre de l'écran
        self.light_rect.center = (self.half_width, self.half_height)
        
        self.fog_surf.blit(self.light_mask, self.light_rect, special_flags=pygame.BLEND_RGBA_SUB)
        
        # Dessine le fog
        self.display_surface.blit(self.fog_surf, (0, 0))


class Game:
    
    def __init__(self):
        pygame.init()
        mixer.init()
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.all_sprites = CameraGroup()
        
        self.player = Player(
            self,
            self.all_sprites,
            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        )
        
        # Timer pour spawn des ennemis
        self.enemy_event = pygame.event.custom_type()
        pygame.time.set_timer(self.enemy_event, 1000)
    
    def spawn_enemy(self):
        # Spawn en cercle autour du joueur
        distance = randint(1000, 1200)
        angle = randint(0, 360)
        
        x = self.player.rect.centerx + distance * cos(radians(angle))
        y = self.player.rect.centery + distance * sin(radians(angle))
        
        Enemy(self, self.all_sprites, (x, y), self.player)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == self.enemy_event:
                self.spawn_enemy()
    
    def update(self, dt):
        self.all_sprites.update(dt)
    
    def draw(self):
        self.screen.fill(BLACK)
        self.all_sprites.custom_draw(self.player)
        pygame.display.flip()
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
