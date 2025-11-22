import pygame
from core.vector2 import Vector2
from core.collider import CircleCollider

class Obstacle:
    def __init__(self, x, y, radius):
        self.collider = CircleCollider(x, y, radius)
        self.collider.position = Vector2(x, y)

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            (140, 140, 180),
            (int(self.collider.position.x), int(self.collider.position.y)),
            self.collider.radius
        )
