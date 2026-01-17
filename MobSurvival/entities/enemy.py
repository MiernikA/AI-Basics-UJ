import pygame
import random
from core.vector2 import Vector2
from core.collider import CircleCollider
from systems.enemy_steering import (
    heading,
    steer_attack,
    steer_hide,
)


class Enemy:
    def __init__(self, x, y, radius=12, min_speed=80, max_speed=130):
        self.position = Vector2(x, y)
        self.collider = CircleCollider(x, y, radius)
        self.collider.position = self.position

        self.state = "hide"
        self.cluster_id = None

        self.max_speed = random.uniform(min_speed, max_speed)
        self.attack_speed = self.max_speed * 1.2
        self.velocity = Vector2()

        self.wander_angle = random.uniform(0, 2 * 3.1415926)
        self.wander_speed = self.max_speed * 0.6
        self.wander_jitter = 2.5

        self.hide_distance = radius + 12
        self.hide_weight = 1.3
        self.separation_weight = 1.4
        self.avoid_weight = 1.6
        self.los_flee_weight = 1.3

        self.bold_timer = random.uniform(10.0, 14.0)
        self.bold_cooldown = random.uniform(4.0, 6.0)
        self.is_bold = False

    def _update_bold_state(self, dt):
        if self.is_bold:
            self.bold_timer -= dt
            if self.bold_timer <= 0:
                self.is_bold = False
                self.bold_cooldown = random.uniform(3.0, 6.0)
        else:
            self.bold_cooldown -= dt
            if self.bold_cooldown <= 0:
                self.is_bold = True
                self.bold_timer = random.uniform(0.5, 1.0)

    def _apply_velocity(self, desired, dt, max_speed):
        desired = desired.limit(max_speed)
        new_vel = self.velocity.mul(0.6).add(desired.mul(0.4))
        if new_vel.length() > max_speed:
            new_vel = new_vel.normalized().mul(max_speed)
        self.velocity = new_vel
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
                self.velocity = away.mul(max(self.velocity.length(), target_speed * 0.8))

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
        else:
            desired, max_speed = steer_hide(self, dt, player, enemies, obstacles, width, height)

        if desired.length() == 0:
            desired = heading(self).mul(self.max_speed * 0.25)

        self._apply_velocity(desired, dt, max_speed)
        self._resolve_obstacle_penetration(obstacles)
        self._resolve_enemy_penetration(enemies)
        self._clamp_to_bounds(width, height)

import pygame
import random
from core.vector2 import Vector2
from core.collider import CircleCollider
from systems.enemy_steering import (
    heading,
    steer_attack,
    steer_hide,
)


class Enemy:
    def __init__(self, x, y, radius=12, min_speed=80, max_speed=130):
        self.position = Vector2(x, y)
        self.collider = CircleCollider(x, y, radius)
        self.collider.position = self.position

        self.state = "hide"
        self.cluster_id = None

        self.max_speed = random.uniform(min_speed, max_speed)
        self.attack_speed = self.max_speed * 1.2
        self.velocity = Vector2()

        self.wander_angle = random.uniform(0, 2 * 3.1415926)
        self.wander_speed = self.max_speed * 0.6
        self.wander_jitter = 2.5

        self.hide_distance = radius + 12
        self.hide_weight = 1.3
        self.separation_weight = 1.4
        self.avoid_weight = 1.6
        self.los_flee_weight = 1.3

        self.bold_timer = random.uniform(10.0, 14.0)
        self.bold_cooldown = random.uniform(4.0, 6.0)
        self.is_bold = False

    def _update_bold_state(self, dt):
        if self.is_bold:
            self.bold_timer -= dt
            if self.bold_timer <= 0:
                self.is_bold = False
                self.bold_cooldown = random.uniform(3.0, 6.0)
        else:
            self.bold_cooldown -= dt
            if self.bold_cooldown <= 0:
                self.is_bold = True
                self.bold_timer = random.uniform(0.5, 1.0)

    def _apply_velocity(self, desired, dt, max_speed):
        desired = desired.limit(max_speed)
        new_vel = self.velocity.mul(0.6).add(desired.mul(0.4))
        if new_vel.length() > max_speed:
            new_vel = new_vel.normalized().mul(max_speed)
        self.velocity = new_vel
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
                self.velocity = away.mul(max(self.velocity.length(), target_speed * 0.8))

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
        else:
            desired, max_speed = steer_hide(self, dt, player, enemies, obstacles, width, height)

        if desired.length() == 0:
            desired = heading(self).mul(self.max_speed * 0.25)

        self._apply_velocity(desired, dt, max_speed)
        self._resolve_obstacle_penetration(obstacles)
        self._resolve_enemy_penetration(enemies)
        self._clamp_to_bounds(width, height)


    def draw(self, screen):
        # if self.state == "hide":
        #     if self.is_bold:
        #         color = (255, 255, 0)
        #     else:
        #         color = (0, 255, 0)
        # elif self.state == "attack":
        color = (255, 50, 50)
        pygame.draw.circle(
            screen,
            color,
            (int(self.position.x), int(self.position.y)),
            self.collider.radius
        )
