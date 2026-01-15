# Module Sprites pour Leak To The Past
# Contient les classes de sprites pour les entités du jeu

import pygame
from settings import TILESIZE, RED


class Player(pygame.sprite.Sprite):
    """Classe représentant le joueur."""
    
    def __init__(self, game, groups, pos):
        """
        Initialise le joueur.
        
        Args:
            game: Référence à l'instance du jeu
            groups: Groupes de sprites auxquels ajouter le joueur
            pos: Position initiale (x, y) en pixels
        """
        super().__init__(groups)
        self.game = game
        
        # Image temporaire (carré rouge pour les tests)
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill(RED)
        
        # Position et hitbox
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.copy()
        
        # Position avec Vector2 pour des mouvements fluides
        self.pos = pygame.math.Vector2(pos)
        self.direction = pygame.math.Vector2(0, 0)
        self.speed = 5
    
    def input(self):
        """Gère les entrées clavier du joueur."""
        pass
    
    def update(self):
        """Met à jour l'état du joueur à chaque frame."""
        self.input()
