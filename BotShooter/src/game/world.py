from __future__ import annotations

import pygame

from src.ai import behavior as ai
from src.game import combat
from src.core.config import AMMO_START_RAIL, BOT_MAX_HEALTH, COLOR_ROCKET, PICKUP_RESPAWN, RAIL_BEAM_TIME
from src.game.entities import Bot, Explosion, RailShot, Resource, Rocket
from src.nav.graph import generate_nav_graph


class World:
    def __init__(self) -> None:
        self.obstacles = build_obstacles()
        self.nav = generate_nav_graph(self.obstacles)
        self.bots = spawn_bots()
        self.resources = build_resources(self.obstacles)
        self.rail_shots: list[RailShot] = []
        self.rockets: list[Rocket] = []
        self.explosions: list[Explosion] = []
        self.time = 0.0
        self.winner_id: int | None = None

    def update(self, dt: float) -> None:
        self.time += dt
        if self.winner_id is not None:
            return

        #respawny
        for bot in self.bots:
            if bot.health <= 0:
                bot.respawn_timer -= dt
                if bot.respawn_timer <= 0.0:
                    respawn_bot(bot)
                continue
            bot.update_timers(dt)
            ai.update_bot_ai(bot, self.bots, self.resources, dt, self.obstacles, self.nav)

        #core
        for bot in self.bots:
            if bot.health <= 0:
                continue
            target = bot.path_target()
            if target is not None:
                old_pos = bot.pos.copy()
                bot.move_towards(target, dt)
                #kolizje
                if overlaps_any(bot, self.bots):
                    bot.pos = old_pos

            #walka
            if bot.state in (ai.STATE_FIGHT, ai.STATE_FIGHT_FOR_LIFE) and bot.target_id is not None:
                target_bot = next((b for b in self.bots if b.bot_id == bot.target_id), None)
                if target_bot:
                    killed = combat.try_fire(
                        bot,
                        target_bot,
                        self.obstacles,
                        self.rockets,
                        self.rail_shots,
                    )
                    if killed:
                        register_kill(self, bot.bot_id, target_bot.bot_id)

        for shot in self.rail_shots:
            shot.timer -= dt
        self.rail_shots = [shot for shot in self.rail_shots if shot.timer > 0.0]
        rocket_kills = combat.update_rockets(
            self.rockets, self.bots, self.obstacles, dt, self.explosions
        )
        for killer_id, victim_id in rocket_kills:
            register_kill(self, killer_id, victim_id)
        self.rockets = [rocket for rocket in self.rockets if rocket.alive]
        self.handle_resources(dt)
        for explosion in self.explosions:
            explosion.timer -= dt
        self.explosions = [explosion for explosion in self.explosions if explosion.timer > 0.0]

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        for poly in self.obstacles:
            pygame.draw.polygon(surface, (70, 85, 96), poly)

        for resource in self.resources:
            if not resource.active:
                continue
            if resource.kind == "health":
                color = (120, 200, 140)
                label_text = "HP"
            elif resource.kind == "rail_ammo":
                color = (200, 200, 120)
                label_text = "Rail"
            else:
                color = (200, 140, 120)
                label_text = "Rocket"
            pygame.draw.circle(surface, color, resource.pos, 8)
            label = font.render(label_text, True, (30, 30, 30))
            label_rect = label.get_rect(center=(resource.pos.x, resource.pos.y - 16))
            surface.blit(label, label_rect)

        for shot in self.rail_shots:
            alpha = max(0.0, min(1.0, shot.timer / RAIL_BEAM_TIME))
            color = (int(240 * alpha + 40), int(220 * alpha + 30), int(130 * alpha + 30))
            pygame.draw.line(surface, color, shot.start, shot.end, 3)

        for rocket in self.rockets:
            pygame.draw.circle(surface, COLOR_ROCKET, rocket.pos, 5)

        for explosion in self.explosions:
            alpha = max(0.0, min(1.0, explosion.timer / 0.25))
            color = (int(255 * alpha), int(180 * alpha), int(80 * alpha))
            radius = int(explosion.radius * (1.0 - alpha * 0.3))
            flash_radius = max(4, int(explosion.radius * 0.35 * alpha))
            flash_color = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
            pygame.draw.circle(surface, flash_color, explosion.pos, flash_radius)
            pygame.draw.circle(surface, color, explosion.pos, radius, 2)

        for bot in self.bots:
            bot.draw(surface, highlight=False)
            if bot.health <= 0:
                pygame.draw.circle(surface, (200, 80, 80), bot.pos, int(bot.radius))
                timer = max(0.0, bot.respawn_timer)
                timer_label = font.render(f"{timer:.1f}s", True, (220, 180, 180))
                timer_rect = timer_label.get_rect(center=(bot.pos.x, bot.pos.y + bot.radius + 8))
                surface.blit(timer_label, timer_rect)
            else:
                label = font.render(str(bot.health), True, (220, 230, 240))
                rect = label.get_rect(center=(bot.pos.x, bot.pos.y - bot.radius - 10))
                surface.blit(label, rect)
                stats = font.render(f"Bot {bot.bot_id}", True, (200, 210, 220))
                stats_rect = stats.get_rect(center=(bot.pos.x, bot.pos.y + bot.radius + 8))
                surface.blit(stats, stats_rect)
                if bot.reload_rail > 0.0 or bot.reload_rocket > 0.0:
                    reload_label = font.render("reloading", True, (220, 200, 160))
                    reload_rect = reload_label.get_rect(center=(bot.pos.x, bot.pos.y - bot.radius - 26))
                    surface.blit(reload_label, reload_rect)

        if self.winner_id is not None:
            label = font.render(f"Winner: Bot {self.winner_id}", True, (255, 220, 160))
            rect = label.get_rect(center=(surface.get_width() / 2, surface.get_height() - 16))
            surface.blit(label, rect)

    def draw_debug(self, surface: pygame.Surface) -> None:
        for node in self.nav.nodes:
            pygame.draw.circle(surface, (40, 50, 60), node.pos, 2)
        for bot in self.bots:
            if bot.path and len(bot.path) > 1:
                pygame.draw.lines(surface, (120, 180, 200), False, bot.path, 2)
    def handle_resources(self, dt: float) -> None:
        for resource in self.resources:
            if not resource.active:
                resource.respawn_timer -= dt
                if resource.respawn_timer <= 0.0:
                    resource.active = True
                continue
            for bot in self.bots:
                if bot.health <= 0:
                    continue
                if (bot.pos - resource.pos).length() <= bot.radius + 8:
                    apply_resource(bot, resource)
                    resource.active = False
                    resource.respawn_timer = PICKUP_RESPAWN
                    break



def build_obstacles() -> list[list[pygame.Vector2]]:
    return [
        [
            pygame.Vector2(250, 140),
            pygame.Vector2(380, 340),           
            pygame.Vector2(380, 220),
            pygame.Vector2(250, 220),
        ],

        [
            pygame.Vector2(440, 100),
            pygame.Vector2(680, 150),           
            pygame.Vector2(740, 310),
            pygame.Vector2(520, 220),
            pygame.Vector2(680, 190),
        ],

        [
            pygame.Vector2(200, 420),
            pygame.Vector2(100, 360),
            pygame.Vector2(220, 350),
            pygame.Vector2(260, 450),
            pygame.Vector2(140, 550),
        ],

        [
            pygame.Vector2(430, 160),
            pygame.Vector2(520, 260),
            pygame.Vector2(520, 340),
            pygame.Vector2(480, 220),
            pygame.Vector2(460, 220),
            pygame.Vector2(430, 440),
        ],

        [
            pygame.Vector2(620, 360),
            pygame.Vector2(820, 360),
            pygame.Vector2(680, 400),
            pygame.Vector2(630, 500),
            pygame.Vector2(820, 440),
            pygame.Vector2(600, 560),
        ],
    ]



def spawn_bots() -> list[Bot]:
    spawn_points = [
        pygame.Vector2(120, 120),
        pygame.Vector2(780, 120),
        pygame.Vector2(140, 500),
        pygame.Vector2(760, 480),
    ]
    bots = []
    for i, pos in enumerate(spawn_points, start=1):
        bots.append(Bot(bot_id=i, pos=pos, spawn_pos=pos.copy()))
    return bots


def build_resources(obstacles) -> list[Resource]:
    spawn_points = [
        pygame.Vector2(120, 300),
        pygame.Vector2(780, 320),
        pygame.Vector2(320, 520),
        pygame.Vector2(450, 480),
        pygame.Vector2(460, 120),
        pygame.Vector2(450, 300),
        pygame.Vector2(160, 420),
        pygame.Vector2(760, 220),
        pygame.Vector2(600, 520),
        pygame.Vector2(200, 120),
        pygame.Vector2(700, 520),
        pygame.Vector2(520, 380),
    ]
    kinds = ["health"] * 3 + ["rail_ammo"] * 5 + ["rocket_ammo"] * 4
    resources: list[Resource] = []
    for kind, pos in zip(kinds, spawn_points, strict=False):
        if not resource_blocked(pos, obstacles):
            resources.append(Resource(kind, pos))
    return resources


def apply_resource(bot: Bot, resource: Resource) -> None:
    if resource.kind == "health":
        bot.health = min(BOT_MAX_HEALTH, bot.health + 35)
    elif resource.kind == "rail_ammo":
        bot.ammo_rail += 3
    elif resource.kind == "rocket_ammo":
        bot.ammo_rocket += 3


def respawn_bot(bot: Bot) -> None:
    bot.pos = bot.spawn_pos.copy()
    bot.health = BOT_MAX_HEALTH
    bot.ammo_rail = AMMO_START_RAIL
    bot.ammo_rocket = 0
    bot.reload_rail = 0.0
    bot.reload_rocket = 0.0
    bot.state = "seek_enemy"
    return


def register_kill(world: World, killer_id: int, victim_id: int) -> None:
    killer = next((b for b in world.bots if b.bot_id == killer_id), None)
    victim = next((b for b in world.bots if b.bot_id == victim_id), None)
    if not killer or not victim:
        return
    if victim.health > 0:
        return
    killer.kills += 1
    victim.deaths += 1
    victim.down(5.0)
    if killer.kills >= 5:
        world.winner_id = killer.bot_id


def resource_blocked(pos: pygame.Vector2, obstacles: list[list[pygame.Vector2]]) -> bool:
    from src.core.geometry import circle_intersects_polygon

    for poly in obstacles:
        if circle_intersects_polygon(pos, 8, poly):
            return True
    return False


def overlaps_any(bot: Bot, bots: list[Bot]) -> bool:
    for other in bots:
        if other.bot_id == bot.bot_id or other.health <= 0:
            continue
        if (bot.pos - other.pos).length() < bot.radius + other.radius:
            return True
    return False
