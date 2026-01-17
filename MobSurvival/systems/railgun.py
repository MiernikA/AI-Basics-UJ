import pygame
from math import cos, sin
from core.vector2 import Vector2


class Railgun:
    def __init__(self, beam_length=1200, color=(255, 40, 40), thickness=2):
        self.beam_length = beam_length
        self.color = color
        self.thickness = thickness

        self.last_beam_start = None
        self.last_beam_end = None
        self.beam_time = 0.1
        self.beam_timer = 0

    def fire(self, player, enemies, obstacles):
        start = player.get_tip()
        angle = player.angle

        raw_end = Vector2(
            start.x + cos(angle) * self.beam_length,
            start.y + sin(angle) * self.beam_length
        )

        hit_enemy, enemy_point, obstacle_point = self._find_first_hit(start, raw_end, enemies, obstacles)

        if hit_enemy:
            end = enemy_point
        elif obstacle_point:
            end = obstacle_point
        else:
            end = raw_end

        self.last_beam_start = start
        self.last_beam_end = end
        self.beam_timer = self.beam_time

        return [hit_enemy] if hit_enemy else []

    def _find_first_hit(self, start, end, enemies, obstacles):
        closest_enemy = None
        closest_enemy_point = None
        closest_enemy_dist = float("inf")

        closest_ob_point = None
        closest_ob_dist = float("inf")

        # Obstacles block the shot
        for ob in obstacles:
            hit_point = self._ray_circle_intersection(start, end, ob)
            if hit_point is not None:
                dist = hit_point.sub(start).length()
                if dist < closest_ob_dist:
                    closest_ob_point = hit_point
                    closest_ob_dist = dist

        # Enemies can be hit but the beam stops at the first one
        for enemy in enemies:
            hit_point = self._ray_circle_intersection(start, end, enemy)
            if hit_point is not None:
                dist = hit_point.sub(start).length()
                if dist < closest_enemy_dist:
                    closest_enemy = enemy
                    closest_enemy_point = hit_point
                    closest_enemy_dist = dist

        # If an obstacle is closer than the nearest enemy, no enemy is hit.
        if closest_ob_point is not None and closest_ob_dist <= closest_enemy_dist:
            return None, None, closest_ob_point

        if closest_enemy:
            return closest_enemy, closest_enemy_point, None

        return None, None, None

    def _ray_circle_intersection(self, start, end, obstacle):
        cx, cy = obstacle.collider.position.x, obstacle.collider.position.y
        r = obstacle.collider.radius

        d = end.sub(start)
        d_len = d.length()
        d_norm = d.normalized()

        f = start.sub(Vector2(cx, cy))

        a = d_norm.x * d_norm.x + d_norm.y * d_norm.y
        b = 2 * (f.x * d_norm.x + f.y * d_norm.y)
        c = f.x * f.x + f.y * f.y - r * r

        disc = b*b - 4*a*c
        if disc < 0:
            return None

        disc = disc ** 0.5

        t1 = (-b - disc) / (2 * a)
        t2 = (-b + disc) / (2 * a)

        t_candidates = [t1, t2]
        best_t = None

        for t in t_candidates:
            if t >= 0:
                hit = start.add(d_norm.mul(t))
                dist = hit.sub(start).length()

                if dist <= d_len:
                    if best_t is None or dist < best_t[0]:
                        best_t = (dist, hit)

        if best_t:
            return best_t[1]

        return None

    def _ray_hits_circle(self, start, end, enemy):
        ray = end.sub(start)
        to_enemy = enemy.position.sub(start)

        ray_len = ray.length()
        if ray_len == 0:
            return False

        ray_dir = ray.normalized()

        proj = to_enemy.x * ray_dir.x + to_enemy.y * ray_dir.y
        proj = max(0, min(ray_len, proj))

        closest = start.add(ray_dir.mul(proj))
        dist = enemy.position.sub(closest).length()

        return dist <= enemy.collider.radius

    def update(self, dt):
        if self.beam_timer > 0:
            self.beam_timer -= dt

    def draw(self, screen):
        if self.beam_timer > 0 and self.last_beam_start and self.last_beam_end:
            pygame.draw.line(
                screen,
                self.color,
                (self.last_beam_start.x, self.last_beam_start.y),
                (self.last_beam_end.x, self.last_beam_end.y),
                self.thickness
            )
