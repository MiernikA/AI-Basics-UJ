from __future__ import annotations

import pygame

from src.core.config import (
    RAIL_BEAM_TIME,
    RAIL_DAMAGE,
    RAIL_RELOAD,
    RAIL_SPREAD_DEG,
    ROCKET_BLAST_RADIUS,
    ROCKET_DAMAGE,
    ROCKET_RELOAD,
    ROCKET_SPEED,
    ROCKET_SPREAD_DEG,
)
from src.game.entities import Bot, Explosion, RailShot, Rocket
from src.core.geometry import line_intersects_polygon, point_in_polygon


def try_fire(
    bot: Bot,
    target: Bot,
    obstacles: list[list[pygame.Vector2]],
    rockets: list[Rocket],
    shots: list[RailShot],
) -> bool:
    if bot.health <= 0 or target.health <= 0:
        return False
    if not has_line_of_sight(bot.pos, target.pos, obstacles):
        return False

    aim_vec = target.pos - bot.pos
    if aim_vec.length_squared() <= 0.0001:
        if bot.reload_rail > 0.0 or bot.ammo_rail <= 0:
            return False
        return fire_rail(bot, target, shots)

    #kierunek
    bot.aim_dir = aim_vec.normalize()
    use_rocket = bot.ammo_rocket > 0 and bot.reload_rocket <= 0.0

    if use_rocket:
        fire_rocket(bot, target, rockets)
        return False
    if bot.reload_rail > 0.0 or bot.ammo_rail <= 0:
        return False
    return fire_rail(bot, target, shots)


def fire_rail(bot: Bot, target: Bot, shots: list[RailShot]) -> bool:
    bot.ammo_rail -= 1
    bot.reload_rail = RAIL_RELOAD

    #kierunek strzalu/faktyczny kierunek do celu
    aim_dir = bot.aim_with_spread(RAIL_SPREAD_DEG)
    shot_vec = target.pos - bot.pos
    if shot_vec.length_squared() <= 0.0001:
        return False
    shot_dir = shot_vec.normalize()
    shots.append(RailShot(bot.pos.copy(), bot.pos + aim_dir * 1200, RAIL_BEAM_TIME))

    #czy trafił?
    if aim_dir.dot(shot_dir) > 0.9:
        prev_health = target.health
        target.health = max(0, target.health - RAIL_DAMAGE)
        return prev_health > 0 and target.health == 0
    return False


def fire_rocket(bot: Bot, target: Bot, rockets: list[Rocket]) -> None:
    bot.ammo_rocket -= 1
    bot.reload_rocket = ROCKET_RELOAD
    aim_dir = bot.aim_with_spread(ROCKET_SPREAD_DEG)
    rockets.append(Rocket(pos=bot.pos.copy(), vel=aim_dir * ROCKET_SPEED, owner_id=bot.bot_id))


def update_rockets(
    rockets: list[Rocket],
    bots: list[Bot],
    obstacles: list[list[pygame.Vector2]],
    dt: float,
    explosions: list[Explosion],
) -> list[tuple[int, int]]:
    kills: list[tuple[int, int]] = []
    for rocket in rockets:
        if not rocket.alive:
            continue
        step = rocket.vel * dt
        rocket.pos += step
        rocket.traveled += step.length()
        if rocket.traveled >= rocket.max_distance:
            kills.extend(explode(rocket, bots, explosions))
            continue
        if hits_wall(rocket.pos, obstacles):
            kills.extend(explode(rocket, bots, explosions))
            continue
        for bot in bots:
            if bot.health <= 0 or bot.bot_id == rocket.owner_id:
                continue
            if (bot.pos - rocket.pos).length() <= bot.radius:
                kills.extend(explode(rocket, bots, explosions))
                break
    return kills


def explode(rocket: Rocket, bots: list[Bot], explosions: list[Explosion]) -> list[tuple[int, int]]:
    if not rocket.alive:
        return []
    rocket.alive = False
    explosions.append(Explosion(rocket.pos.copy(), 0.25, ROCKET_BLAST_RADIUS))
    kills: list[tuple[int, int]] = []

    #obszarowe obrazenia
    for bot in bots:
        dist = (bot.pos - rocket.pos).length()
        if dist <= ROCKET_BLAST_RADIUS:
            scale = max(0.2, 1.0 - dist / ROCKET_BLAST_RADIUS)
            damage = int(ROCKET_DAMAGE * scale)
            prev_health = bot.health
            bot.health = max(0, bot.health - damage)
            if prev_health > 0 and bot.health == 0:
                kills.append((rocket.owner_id, bot.bot_id))
    return kills


def hits_wall(pos: pygame.Vector2, obstacles: list[list[pygame.Vector2]]) -> bool:
    for poly in obstacles:
        if point_in_polygon(pos, poly):
            return True
    return False


def has_line_of_sight(
    start: pygame.Vector2, end: pygame.Vector2, obstacles: list[list[pygame.Vector2]]
) -> bool:
    for poly in obstacles:
        if line_intersects_polygon(start, end, poly):
            return False
    return True

def is_reloading(bot: Bot) -> bool:
    no_rail = bot.ammo_rail <= 0 or bot.reload_rail > 0.0
    no_rocket = bot.ammo_rocket <= 0 or bot.reload_rocket > 0.0
    return no_rail and no_rocket