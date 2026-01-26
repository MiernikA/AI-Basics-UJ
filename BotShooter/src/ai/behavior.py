from __future__ import annotations

import random
from collections import deque

import pygame

from src.nav.astar import astar
from src.game.entities import Bot, Resource
from src.core.geometry import line_intersects_polygon
from src.nav.graph import NavGraph
from src.game.combat import is_reloading

STATE_SEEK = "seek_enemy"
STATE_FLEE = "flee"
STATE_GATHER = "gather"
STATE_FIGHT = "fight"
STATE_RUN = "run"
STATE_FIGHT_FOR_LIFE = "fight_for_life"

# 1. STATE_RUN
#    Warunki:
#    - istnieje wróg
#    - bot się przeładowuje
#    - bot ma amunicję
#    - wróg jest w linii widzenia
# ------------------------------------------------------------
#
# 2. STATE_FIGHT_FOR_LIFE
#    Warunki:
#    - health < 35
#    - istnieje wróg
#    - bot ma amunicję
#
# ------------------------------------------------------------
#
# 3. STATE_FLEE
#    Warunki:
#    - health < 35
#    - brak amunicji LUB brak przeciwnika
#
# ------------------------------------------------------------
#
# 4. STATE_GATHER
#    Warunki:
#    - brak amunicji (ammo_total <= 0)
#
# ------------------------------------------------------------
#
# 5. STATE_FIGHT
#    Warunki:
#    - istnieje wróg
#    - wróg w linii widzenia
#    - bot ma amunicję
#    - health >= 35
#
# ------------------------------------------------------------
#
# 6. STATE_SEEK
#    Warunki:
#    - istnieje wróg
#    - brak linii widzenia
#    - bot ma amunicję
#
# ------------------------------------------------------------
#
# 7. FALLBACK / WANDER
#    Warunki:
#    - brak wroga
#    - brak celu
#


def update_bot_ai(
    bot: Bot,
    bots: list[Bot],
    resources: list[Resource],
    dt: float,
    obstacles: list[list[pygame.Vector2]],
    nav: NavGraph,
) -> None:
    if not hasattr(bot, "repath_timer"):
        bot.repath_timer = 0.0

    bot.repath_timer -= dt
    ammo_total = bot.ammo_rail + bot.ammo_rocket
    enemy = closest_bot(bot, bots)

    if enemy and is_reloading(bot) and has_line_of_sight(bot.pos, enemy.pos, obstacles) and ammo_total > 0:
        bot.state = STATE_RUN
        bot.target_id = enemy.bot_id

        if bot.repath_timer <= 0:
            assign_flee_path(bot, nav, enemy)
            bot.repath_timer = 0.5

        return

    if bot.health < 35:
        bot.target_id = enemy.bot_id if enemy else None
        health_target = closest_resource_within_hops(
            bot, resources, nav, max_hops=30, kind_filter=("health",)
        )
        if health_target:
            bot.state = STATE_RUN

        if ammo_total > 0 and enemy is not None:
            bot.state = STATE_FIGHT_FOR_LIFE
            if bot.repath_timer <= 0:
                assign_path(bot, nav, enemy.pos)
                bot.repath_timer = 0.2
            return

        bot.state = STATE_FLEE
        if enemy is not None:
            if bot.repath_timer <= 0:
                assign_flee_path(bot, nav, enemy)
                bot.repath_timer = 0.4
        elif bot.path_target() is None:
            assign_random_path(bot, nav)
        return

    if ammo_total <= 0:
        bot.state = STATE_GATHER
        bot.target_id = None
        target = closest_resource(bot, resources, kind_filter=("rail_ammo", "rocket_ammo"))
        if target:
            if bot.repath_timer <= 0 or (bot.goal and (bot.goal - target.pos).length_squared() > 1.0):
                assign_path(bot, nav, target.pos)
                bot.repath_timer = 0.5
        elif bot.path_target() is None:
            assign_random_path(bot, nav)
        return

    if enemy and has_line_of_sight(bot.pos, enemy.pos, obstacles):
        bot.state = STATE_FIGHT
        bot.target_id = enemy.bot_id
        if bot.repath_timer <= 0:
            assign_path(bot, nav, enemy.pos)
            bot.repath_timer = 0.3

        if bot.path_target() is None:
            assign_random_path(bot, nav)
        return

    bot.state = STATE_SEEK
    bot.target_id = None
    if enemy:
        if bot.repath_timer <= 0:
            assign_path(bot, nav, enemy.pos)
            bot.repath_timer = 0.25 + random.uniform(0, 0.1)
    elif bot.path_target() is None:
        assign_random_path(bot, nav)

    if ammo_total <= 0:
        bot.state = STATE_GATHER
        bot.target_id = None
        target = closest_resource(bot, resources, kind_filter=("rail_ammo", "rocket_ammo"))
        if target:
            assign_path(bot, nav, target.pos)
        elif bot.path_target() is None:
            assign_random_path(bot, nav)
        return

    if enemy and has_line_of_sight(bot.pos, enemy.pos, obstacles):
        bot.state = STATE_FIGHT
        bot.target_id = enemy.bot_id
        assign_path(bot, nav, enemy.pos)
        if bot.path_target() is None:
            assign_random_path(bot, nav)
        return

    bot.state = STATE_SEEK
    bot.target_id = None
    if enemy:
        assign_path(bot, nav, enemy.pos)
    elif bot.path_target() is None:
        assign_random_path(bot, nav)


def assign_random_path(bot: Bot, nav: NavGraph) -> None:
    if not nav.nodes:
        return
    start_node = nav.nearest_node(bot.pos)
    if not start_node:
        return
    if len(nav.nodes) == 1:
        bot.set_path([start_node.pos])
        return
    goal_node = random.choice(nav.nodes)
    if goal_node.index == start_node.index:
        goal_node = random.choice(nav.nodes)
    path_nodes = astar(nav, start_node, goal_node)
    bot.set_path([node.pos for node in path_nodes])


def assign_path(bot: Bot, nav: NavGraph, destination: pygame.Vector2) -> None:
    if bot.goal and bot.path_target():
        dist_sq = (bot.goal - destination).length_squared()
        if dist_sq < 9.0:
            return

    start_node = None

    current_target = bot.path_target()
    if current_target:
        start_node = nav.nearest_node(current_target)

        if start_node and (start_node.pos - current_target).length_squared() > 1.0:
            start_node = nav.nearest_node(bot.pos)
    else:
        start_node = nav.nearest_node(bot.pos)

    if not start_node:
        start_node = nav.nearest_node(bot.pos)

    goal_node = nav.nearest_node(destination)

    if not start_node or not goal_node:
        return

    # Optymalizacja: jeśli start i cel to ten sam węzeł
    if start_node.index == goal_node.index:
        bot.set_path([destination])
        bot.goal = destination
        return

    path_nodes = astar(nav, start_node, goal_node)
    path_points = [node.pos for node in path_nodes]

    if path_points:
        path_points[-1] = destination

    bot.set_path(path_points)
    bot.goal = destination


def closest_resource(
    bot: Bot, resources: list[Resource], kind_filter: tuple[str, ...] | None = None
) -> Resource | None:
    if kind_filter is None:
        active = [r for r in resources if r.active]
    else:
        active = [r for r in resources if r.active and r.kind in kind_filter]
    if not active:
        return None
    return min(active, key=lambda r: (r.pos - bot.pos).length_squared())


def closest_bot(bot: Bot, bots: list[Bot]) -> Bot | None:
    others = [b for b in bots if b.bot_id != bot.bot_id and b.health > 0]
    if not others:
        return None
    return min(others, key=lambda b: (b.pos - bot.pos).length_squared())


def assign_flee_path(bot: Bot, nav: NavGraph, enemy: Bot) -> None:
    if not nav.nodes:
        return
    start_node = nav.nearest_node(bot.pos)
    if not start_node:
        return
    sample = nav.nodes if len(nav.nodes) <= 80 else random.sample(nav.nodes, 80)
    goal_node = max(sample, key=lambda n: (n.pos - enemy.pos).length_squared())
    path_nodes = astar(nav, start_node, goal_node)
    bot.set_path([node.pos for node in path_nodes])


def closest_resource_within_hops(
    bot: Bot,
    resources: list[Resource],
    nav: NavGraph,
    max_hops: int,
    kind_filter: tuple[str, ...],
) -> Resource | None:
    start_node = nav.nearest_node(bot.pos)
    if not start_node:
        return None
    resource_nodes: list[tuple[Resource, int]] = []
    for resource in resources:
        if not resource.active or resource.kind not in kind_filter:
            continue
        node = nav.nearest_node(resource.pos)
        if node:
            resource_nodes.append((resource, node.index))
    if not resource_nodes:
        return None

    queue = deque([(start_node.index, 0)])
    visited = {start_node.index}
    hits: list[Resource] = []
    while queue:
        current_index, depth = queue.popleft()
        if depth > max_hops:
            continue
        for resource, node_index in resource_nodes:
            if node_index == current_index:
                hits.append(resource)
        if depth == max_hops:
            continue
        for neighbor in nav.edges.get(current_index, []):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            queue.append((neighbor, depth + 1))
    if not hits:
        return None
    return min(hits, key=lambda r: (r.pos - bot.pos).length_squared())


def has_line_of_sight(
    start: pygame.Vector2, end: pygame.Vector2, obstacles: list[list[pygame.Vector2]]
) -> bool:
    for poly in obstacles:
        if line_intersects_polygon(start, end, poly):
            return False
    return True
