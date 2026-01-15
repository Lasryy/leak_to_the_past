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
        self.speed = 300  # Pixels par seconde
    
    def input(self):
        """Gère les entrées clavier du joueur (ZQSD ou flèches)."""
        keys = pygame.key.get_pressed()
        
        # Réinitialise la direction
        self.direction.x = 0
        self.direction.y = 0
        
        # Mouvement vertical (Z/S ou Haut/Bas)
        if keys[pygame.K_z] or keys[pygame.K_UP]:
            self.direction.y = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.direction.y = 1
        
        # Mouvement horizontal (Q/D ou Gauche/Droite)
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            self.direction.x = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.direction.x = 1
        
        # Normalisation du vecteur pour éviter d'aller plus vite en diagonale
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
    
    def update(self, dt):
        """
        Met à jour l'état du joueur à chaque frame.
        
        Args:
            dt: Delta time en secondes
        """
        self.input()
        
        # Applique le déplacement avec delta time
        self.pos += self.direction * self.speed * dt
        
        # Met à jour le rect pour l'affichage
        self.rect.x = round(self.pos.x)
        self.rect.y = round(self.pos.y)
        self.hitbox.center = self.rect.center
