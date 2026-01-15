"""
Leak To The Past - Module Principal du Jeu
Un projet de jeu basé sur Pygame
"""

import pygame
from pygame import mixer
from settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE


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
    
    def handle_events(self):
        """Gère tous les événements pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
    
    def update(self):
        """Met à jour l'état du jeu."""
        pass
    
    def draw(self):
        """Affiche les objets du jeu à l'écran."""
        self.screen.fill((0, 0, 0))
        pygame.display.flip()
    
    def run(self):
        """Boucle principale du jeu."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
