from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import pygame

from src.core.config import BOT_RADIUS, MAP_BOUNDS, NAV_SEED, NAV_STEP
from src.core.geometry import circle_intersects_polygon


@dataclass(frozen=True)
class NavNode:
    index: int
    pos: pygame.Vector2


class NavGraph:
    def __init__(self, nodes: list[NavNode], edges: dict[int, list[int]]):
        self.nodes = nodes
        self.edges = edges

    def nearest_node(self, pos: pygame.Vector2) -> NavNode | None:
        best = None
        best_dist = float("inf")
        for node in self.nodes:
            dist = (node.pos - pos).length_squared()
            if dist < best_dist:
                best_dist = dist
                best = node
        return best


def generate_nav_graph(obstacles: list[list[pygame.Vector2]]) -> NavGraph:
    step = NAV_STEP
    radius = BOT_RADIUS

    def key(pos: pygame.Vector2) -> tuple[int, int]:
        return (int(round(pos.x)), int(round(pos.y)))

    #nie budujemy grafu na przeszkodach
    def valid(pos: pygame.Vector2) -> bool:
        if not MAP_BOUNDS.collidepoint(pos.x, pos.y):
            return False
        for poly in obstacles:
            if circle_intersects_polygon(pos, radius, poly):
                return False
        return True

    #kolejka do BFS
    nodes: list[NavNode] = []
    edges: dict[int, list[int]] = {}
    visited: dict[tuple[int, int], int] = {}

    queue = deque()
    if valid(NAV_SEED):
        queue.append(NAV_SEED)
        visited[key(NAV_SEED)] = 0
        nodes.append(NavNode(0, NAV_SEED))

    directions = [
        pygame.Vector2(step, 0),
        pygame.Vector2(-step, 0),
        pygame.Vector2(0, step),
        pygame.Vector2(0, -step),
        pygame.Vector2(step, step),
        pygame.Vector2(step, -step),
        pygame.Vector2(-step, step),
        pygame.Vector2(-step, -step),
    ]

    #BFS
    while queue:
        current = queue.popleft()
        current_index = visited[key(current)]
        edges.setdefault(current_index, [])
        for delta in directions:
            candidate = current + delta
            c_key = key(candidate)
            if not valid(candidate):
                continue
            if c_key not in visited:
                index = len(nodes)
                visited[c_key] = index
                nodes.append(NavNode(index, candidate))
                queue.append(candidate)
            neighbor_index = visited[c_key]
            edges[current_index].append(neighbor_index)

    return NavGraph(nodes, edges)
