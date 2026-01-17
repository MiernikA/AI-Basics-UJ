from __future__ import annotations

from dataclasses import dataclass, field
import random

import pygame

from src.core.config import (
    AMMO_START_RAIL,
    AMMO_START_ROCKET,
    BOT_MAX_HEALTH,
    BOT_RADIUS,
    BOT_SPEED,
    COLOR_BOT,
    COLOR_BOT_ENEMY,
    COLOR_ROCKET,
    PICKUP_RADIUS,
)
from src.core.geometry import rotate_vector


@dataclass
class Pickup:
    kind: str
    pos: pygame.Vector2
    active: bool = True
    respawn_timer: float = 0.0


@dataclass
class Rocket:
    pos: pygame.Vector2
    vel: pygame.Vector2
    owner_id: int
    alive: bool = True
    traveled: float = 0.0
    max_distance: float = 520.0


@dataclass
class RailShot:
    start: pygame.Vector2
    end: pygame.Vector2
    timer: float


@dataclass
class Resource:
    kind: str
    pos: pygame.Vector2
    active: bool = True
    respawn_timer: float = 0.0


@dataclass
class Explosion:
    pos: pygame.Vector2
    timer: float
    radius: float


@dataclass
class Bot:
    bot_id: int
    pos: pygame.Vector2
    spawn_pos: pygame.Vector2
    color: tuple[int, int, int] = COLOR_BOT
    radius: float = BOT_RADIUS
    speed: float = BOT_SPEED
    health: int = BOT_MAX_HEALTH
    ammo_rail: int = AMMO_START_RAIL
    ammo_rocket: int = AMMO_START_ROCKET
    reload_rail: float = 0.0
    reload_rocket: float = 0.0
    respawn_timer: float = 0.0
    kills: int = 0
    deaths: int = 0
    target_id: int | None = None
    state: str = "seek_enemy"
    path: list[pygame.Vector2] = field(default_factory=list)
    path_index: int = 0
    goal: pygame.Vector2 | None = None
    aim_dir: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(1, 0))
    desired_dir: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(1, 0))
    last_seen_enemy: pygame.Vector2 | None = None
    last_pos: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0, 0))
    stuck_time: float = 0.0

    def draw(self, surface: pygame.Surface, highlight: bool = False) -> None:
        color = COLOR_BOT_ENEMY if highlight else self.color
        pygame.draw.circle(surface, color, self.pos, int(self.radius))

    def update_timers(self, dt: float) -> None:
        self.reload_rail = max(0.0, self.reload_rail - dt)
        self.reload_rocket = max(0.0, self.reload_rocket - dt)

    def down(self, respawn_time: float) -> None:
        self.health = 0
        self.respawn_timer = respawn_time
        self.path = []
        self.path_index = 0
        self.goal = None

    def move_towards(self, target: pygame.Vector2, dt: float) -> None:
        direction = target - self.pos
        dist = direction.length()
        if dist <= 1.0:
            self.advance_path()
            return
        self.desired_dir = direction.normalize()
        step = self.speed * dt
        if step >= dist:
            self.pos = target.copy()
            self.advance_path()
        else:
            self.pos += self.desired_dir * step
        self.aim_dir = self.desired_dir

    def set_path(self, nodes: list[pygame.Vector2]) -> None:
        self.path = nodes
        self.path_index = 0
        self.goal = nodes[-1] if nodes else None

    def path_target(self) -> pygame.Vector2 | None:
        if self.path_index >= len(self.path):
            return None
        return self.path[self.path_index]

    def advance_path(self) -> None:
        if not self.path:
            return
        if self.path_index < len(self.path) - 1:
            self.path_index += 1
        else:
            self.path_index = len(self.path)

    def aim_with_spread(self, degrees: float) -> pygame.Vector2:
        jitter = random.uniform(-degrees, degrees)
        return rotate_vector(self.aim_dir, jitter).normalize()
