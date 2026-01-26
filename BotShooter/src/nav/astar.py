from __future__ import annotations

import heapq
from src.nav.graph import NavGraph, NavNode


def astar(graph: NavGraph, start: NavNode, goal: NavNode) -> list[NavNode]:
    # f(n) = g(n) + h(n)
    # g(n) – koszt dojścia od startu do węzła n - ile juz przeszla sciezka
    # h(n) – przybliżony koszt dojścia z n do celu (heurystyka) - ile jeszcze trzeba przejsc

    if start.index == goal.index:
        return [start]

    # Zbiór węzłów do odwiedzenia
    open_set: list[tuple[float, int]] = []
    heapq.heappush(open_set, (0.0, start.index))

    came_from: dict[int, int] = {}

    #podlicz koszty
    g_score: dict[int, float] = {start.index: 0.0}
    f_score: dict[int, float] = {
        start.index: (start.pos - goal.pos).length()
    }

    in_open = {start.index}

    while open_set:
        # Pobierz najtanszy wezel
        _, current_index = heapq.heappop(open_set)
        in_open.discard(current_index)

        if current_index == goal.index:
            return reconstruct_path(graph, came_from, current_index)

        current_node = graph.nodes[current_index]


        for neighbor_index in graph.edges.get(current_index, []):
            neighbor_node = graph.nodes[neighbor_index]

            # Oblicz koszt dojścia do sąsiada
            tentative = g_score[current_index] + (
                neighbor_node.pos - current_node.pos
            ).length()

            # Szukamy taniej
            if tentative < g_score.get(neighbor_index, float("inf")):
                came_from[neighbor_index] = current_index
                g_score[neighbor_index] = tentative

                f_score[neighbor_index] = tentative + (
                    neighbor_node.pos - goal.pos
                ).length()

                if neighbor_index not in in_open:
                    heapq.heappush(
                        open_set,
                        (f_score[neighbor_index], neighbor_index),
                    )
                    in_open.add(neighbor_index)

    return []


def reconstruct_path(
    graph: NavGraph, came_from: dict[int, int], current_index: int
) -> list[NavNode]:
    path = [graph.nodes[current_index]]
    while current_index in came_from:
        current_index = came_from[current_index]
        path.append(graph.nodes[current_index])
    path.reverse()
    return path
