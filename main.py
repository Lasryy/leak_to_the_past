"""
Leak To The Past - Module Principal du Jeu
"""

import pygame
from pygame import mixer
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE, BLACK, TILESIZE
from sprites import Player


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
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
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
