import pygame
import random

from core.collider import CircleCollider
from core.vector2 import Vector2
from systems.enemy_steering import (
    heading,
    steer_attack,
    steer_bold,
    steer_hide,
)


class Enemy:
    HIDE_COLOR = (80, 220, 120)
    BOLD_COLOR = (255, 210, 70)
    ATTACK_COLOR = (255, 70, 70)
    RANGE_ALPHA = 40
    DIRECTION_ALPHA = 85
    TARGET_ALPHA = 70

    def __init__(self, x, y, radius=12, min_speed=135, max_speed=210):
        self.position = Vector2(x, y)
        self.collider = CircleCollider(x, y, radius)
        self.collider.position = self.position

        self.state = "hide"
        self.cluster_id = None

        self.max_speed = random.uniform(min_speed, max_speed)
        self.attack_speed = self.max_speed * 1.35
        self.mass = 1.0
        self.max_force = self.max_speed * 3.2
        self.velocity = Vector2()

        self.min_detection_box = radius * 3.0
        self.detection_box_scale = radius * 6.0
        self.brake_weight = 0.7

        self.separation_weight = 1.4
        self.avoid_weight = 1.6
        self.los_flee_weight = 1.3
        self.group_range = 230
        self.debug_target = None

        self.bold_timer = random.uniform(10.0, 14.0)
        self.bold_cooldown = random.uniform(3.0, 5.0)
        self.is_bold = False

    def _update_bold_state(self, dt):
        if self.is_bold:
            self.bold_timer -= dt
            if self.bold_timer <= 0:
                self.is_bold = False
                self.bold_cooldown = random.uniform(3.0, 5.5)
        else:
            self.bold_cooldown -= dt
            if self.bold_cooldown <= 0:
                self.is_bold = True
                self.bold_timer = random.uniform(4.5, 7.0)

    def _apply_steering(self, steering_force, dt, max_speed):
        steering_force = steering_force.limit(self.max_force)
        acceleration = steering_force.div(self.mass)
        self.velocity = self.velocity.add(acceleration.mul(dt))
        self.velocity = self.velocity.mul(0.985)
        if self.velocity.length() > max_speed:
            self.velocity = self.velocity.normalized().mul(max_speed)
        self.position = self.position.add(self.velocity.mul(dt))
        self.collider.position = self.position

    def _resolve_obstacle_penetration(self, obstacles):
        r = self.collider.radius
        for ob in obstacles:
            diff = self.position.sub(ob.collider.position)
            dist = diff.length()
            min_dist = r + ob.collider.radius
            if 0 < dist < min_dist:
                push = diff.normalized().mul(min_dist - dist)
                self.position = self.position.add(push)
                self.collider.position = self.position
                target_speed = self.attack_speed if self.state == "attack" else self.max_speed
                away = push.normalized()
                self.velocity = away.mul(max(self.velocity.length(), target_speed * 0.65))

    def _resolve_enemy_penetration(self, enemies):
        r = self.collider.radius
        for other in enemies:
            if other is self:
                continue
            diff = self.position.sub(other.position)
            dist = diff.length()
            min_dist = r + other.collider.radius
            if 0 < dist < min_dist:
                push = diff.normalized().mul((min_dist - dist) * 0.5)
                self.position = self.position.add(push)
                self.collider.position = self.position
                self.velocity = self.velocity.add(push.normalized().mul(self.max_speed * 0.1))

    def _clamp_to_bounds(self, width, height):
        r = self.collider.radius
        target_speed = self.attack_speed if self.state == "attack" else self.max_speed
        if self.position.x - r < 0:
            self.position.x = r
            self.velocity.x = abs(target_speed * 0.8)
        elif self.position.x + r > width:
            self.position.x = width - r
            self.velocity.x = -abs(target_speed * 0.8)

        if self.position.y - r < 0:
            self.position.y = r
            self.velocity.y = abs(target_speed * 0.8)
        elif self.position.y + r > height:
            self.position.y = height - r
            self.velocity.y = -abs(target_speed * 0.8)

        self.collider.position = self.position

    def update(self, dt, width, height, obstacles, enemies, player):
        self._update_bold_state(dt)

        if self.state == "attack":
            desired, max_speed = steer_attack(self, player, enemies, obstacles, width, height)
        elif self.is_bold:
            desired, max_speed = steer_bold(self, player, enemies, obstacles, width, height)
        else:
            desired, max_speed = steer_hide(self, dt, player, enemies, obstacles, width, height)

        if desired.length() == 0:
            desired = heading(self).mul(self.max_force * 0.1)

        self._apply_steering(desired, dt, max_speed)
        self._resolve_obstacle_penetration(obstacles)
        self._resolve_enemy_penetration(enemies)
        self._clamp_to_bounds(width, height)

    def get_display_state(self):
        if self.state == "attack":
            return "attack"
        if self.is_bold:
            return "bold"
        return "hide"

    def get_color(self):
        state = self.get_display_state()
        if state == "attack":
            return self.ATTACK_COLOR
        if state == "bold":
            return self.BOLD_COLOR
        return self.HIDE_COLOR

    def draw(self, screen):
        pygame.draw.circle(
            screen,
            self.get_color(),
            (int(self.position.x), int(self.position.y)),
            self.collider.radius
        )

    def draw_debug(self, screen, group_range):
        pos = (int(self.position.x), int(self.position.y))
        color = self.get_color()
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

        pygame.draw.circle(overlay, (*color, self.RANGE_ALPHA), pos, int(group_range), 1)

        if self.velocity.length() > 0:
            forward = self.velocity.normalized()
            tip = self.position.add(forward.mul(18))
            side = forward.perp()
            left = self.position.add(forward.mul(8)).add(side.mul(5))
            right = self.position.add(forward.mul(8)).sub(side.mul(5))
            points = [
                (int(tip.x), int(tip.y)),
                (int(left.x), int(left.y)),
                (int(right.x), int(right.y)),
            ]
            pygame.draw.polygon(overlay, (*color, self.DIRECTION_ALPHA), points)

        if self.debug_target is not None:
            target_pos = (int(self.debug_target.x), int(self.debug_target.y))
            pygame.draw.line(overlay, (180, 220, 255, self.TARGET_ALPHA), pos, target_pos, 1)
            pygame.draw.circle(overlay, (180, 220, 255, self.TARGET_ALPHA), target_pos, 4, 1)

        screen.blit(overlay, (0, 0))
