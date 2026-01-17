from __future__ import annotations

import random
from collections import deque

import pygame

from src.nav.astar import astar
from src.game.entities import Bot, Resource
from src.core.geometry import line_intersects_polygon
from src.nav.graph import NavGraph

STATE_SEEK = "seek_enemy"
STATE_FLEE = "flee"
STATE_GATHER = "gather"
STATE_FIGHT = "fight"
STATE_RUN = "run"
STATE_FIGHT_FOR_LIFE = "fight_for_life"


def update_bot_ai(
    bot: Bot,
    bots: list[Bot],
    resources: list[Resource],
    dt: float,
    obstacles: list[list[pygame.Vector2]],
    nav: NavGraph,
) -> None:
    ammo_total = bot.ammo_rail + bot.ammo_rocket
    enemy = closest_bot(bot, bots)
    if bot.health < 35:
        bot.target_id = enemy.bot_id if enemy else None
        health_target = closest_resource_within_hops(
            bot, resources, nav, max_hops=30, kind_filter=("health",)
        )
        if health_target:
            bot.state = STATE_RUN
            assign_path(bot, nav, health_target.pos)
            return
        if ammo_total > 0 and enemy is not None:
            bot.state = STATE_FIGHT_FOR_LIFE
            assign_path(bot, nav, enemy.pos)
            return
        bot.state = STATE_FLEE
        if enemy is not None:
            assign_flee_path(bot, nav, enemy)
        elif bot.path_target() is None:
            assign_random_path(bot, nav)
        return

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
    start_node = nav.nearest_node(bot.pos)
    goal_node = nav.nearest_node(destination)
    if not start_node or not goal_node:
        return
    if bot.goal and (bot.goal - goal_node.pos).length_squared() < 9.0 and bot.path_target():
        return
    path_nodes = astar(nav, start_node, goal_node)
    bot.set_path([node.pos for node in path_nodes])


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
