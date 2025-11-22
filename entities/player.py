import pygame
from math import atan2, cos, sin
from core.vector2 import Vector2
from core.collider import CircleCollider


class Player:
    def __init__(self, x, y, radius=25, speed=250):
        self.position = Vector2(x, y)
        self.speed = speed
        self.angle = 0

        self.collider = CircleCollider(x, y, radius)
        self.collider.position = self.position

    def update(self, dt, keys, mouse_pos):
        direction = Vector2()

        if keys[pygame.K_w]: direction.y -= 1
        if keys[pygame.K_s]: direction.y += 1
        if keys[pygame.K_a]: direction.x -= 1
        if keys[pygame.K_d]: direction.x += 1

        velocity = direction.normalized().mul(self.speed * dt)
        self.position = self.position.add(velocity)
        self.collider.position = self.position

        mx, my = mouse_pos
        self.angle = atan2(my - self.position.y, mx - self.position.x)

    def draw(self, screen):
        p = self.position
        r = self.collider.radius

        tip = (p.x + cos(self.angle) * r,
               p.y + sin(self.angle) * r)
        left = (p.x + cos(self.angle + 2.5) * r * 0.8,
                p.y + sin(self.angle + 2.5) * r * 0.8)
        right = (p.x + cos(self.angle - 2.5) * r * 0.8,
                 p.y + sin(self.angle - 2.5) * r * 0.8)

        pygame.draw.polygon(screen, (255, 220, 120), [tip, left, right])
