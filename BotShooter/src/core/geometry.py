import math

import pygame

from .config import EPS


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def distance_point_to_segment(point: pygame.Vector2, a: pygame.Vector2, b: pygame.Vector2) -> float:
    ab = b - a
    denom = ab.length_squared()
    if denom <= EPS:
        return (point - a).length()
    t = clamp((point - a).dot(ab) / denom, 0.0, 1.0)
    closest = a + ab * t
    return (point - closest).length()


def point_in_polygon(point: pygame.Vector2, polygon: list[pygame.Vector2]) -> bool:
    inside = False
    count = len(polygon)
    if count < 3:
        return False
    j = count - 1
    for i in range(count):
        pi = polygon[i]
        pj = polygon[j]
        intersects = ((pi.y > point.y) != (pj.y > point.y)) and (
            point.x < (pj.x - pi.x) * (point.y - pi.y) / (pj.y - pi.y + EPS) + pi.x
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def circle_intersects_polygon(
    center: pygame.Vector2, radius: float, polygon: list[pygame.Vector2]
) -> bool:
    if point_in_polygon(center, polygon):
        return True
    count = len(polygon)
    for i in range(count):
        a = polygon[i]
        b = polygon[(i + 1) % count]
        if distance_point_to_segment(center, a, b) <= radius:
            return True
    return False


def line_intersects_polygon(
    start: pygame.Vector2, end: pygame.Vector2, polygon: list[pygame.Vector2]
) -> bool:
    if point_in_polygon(start, polygon) or point_in_polygon(end, polygon):
        return True
    count = len(polygon)
    for i in range(count):
        a = polygon[i]
        b = polygon[(i + 1) % count]
        if segments_intersect(start, end, a, b):
            return True
    return False


def segments_intersect(a1: pygame.Vector2, a2: pygame.Vector2, b1: pygame.Vector2, b2: pygame.Vector2) -> bool:
    def ccw(p1: pygame.Vector2, p2: pygame.Vector2, p3: pygame.Vector2) -> bool:
        return (p3.y - p1.y) * (p2.x - p1.x) > (p2.y - p1.y) * (p3.x - p1.x)

    return (ccw(a1, b1, b2) != ccw(a2, b1, b2)) and (ccw(a1, a2, b1) != ccw(a1, a2, b2))


def rotate_vector(vector: pygame.Vector2, degrees: float) -> pygame.Vector2:
    radians = math.radians(degrees)
    return pygame.Vector2(
        vector.x * math.cos(radians) - vector.y * math.sin(radians),
        vector.x * math.sin(radians) + vector.y * math.cos(radians),
    )
