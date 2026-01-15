"""
Leak To The Past - Module Principal du Jeu
Un projet de jeu basé sur Pygame
"""

import pygame
from pygame import mixer
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE, BLACK
from sprites import Player


class CameraGroup(pygame.sprite.Group):
    """Groupe de sprites avec gestion de la caméra centrée sur le joueur."""
    
    def __init__(self):
        """Initialise le groupe caméra."""
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        
        # Centre de l'écran
        self.half_width = self.display_surface.get_width() // 2
        self.half_height = self.display_surface.get_height() // 2
        
        # Décalage de la caméra
        self.offset = pygame.math.Vector2()
    
    def custom_draw(self, player):
        """
        Dessine tous les sprites avec décalage selon la position du joueur.
        
        Args:
            player: Le sprite joueur à suivre
        """
        # Calcul du décalage pour centrer la caméra sur le joueur
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height
        
        # Dessine chaque sprite avec le décalage
        for sprite in self.sprites():
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)


class Game:
    """Classe principale gérant l'initialisation, la boucle de jeu et le rendu."""
    
    def __init__(self):
        """Initialise pygame, le mixer audio et les composants du jeu."""
        pygame.init()
        mixer.init()
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Groupe de sprites avec caméra
        self.all_sprites = CameraGroup()
        
        # Création du joueur au centre de l'écran
        self.player = Player(
            self,
            self.all_sprites,
            (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        )
    
    def handle_events(self):
        """Gère tous les événements pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def update(self, dt):
        """
        Met à jour l'état du jeu.
        
        Args:
            dt: Delta time en secondes
        """
        self.all_sprites.update(dt)
    
    def draw(self):
        """Affiche les objets du jeu à l'écran."""
        self.screen.fill(BLACK)
        self.all_sprites.custom_draw(self.player)
        pygame.display.flip()
    
    def run(self):
        """Boucle principale du jeu."""
        while self.running:
            # Calcul du delta time (en secondes)
            dt = self.clock.tick(FPS) / 1000
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
