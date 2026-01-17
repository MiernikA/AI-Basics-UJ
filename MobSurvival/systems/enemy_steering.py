import math
import random

from core.vector2 import Vector2


def heading(enemy):
    if enemy.velocity.length() == 0:
        return Vector2(1, 0)
    return enemy.velocity.normalized()


def wander(enemy, dt):
    enemy.wander_angle += random_jitter(enemy) * dt
    return Vector2(math.cos(enemy.wander_angle), math.sin(enemy.wander_angle)).mul(enemy.wander_speed)


def seek(enemy, target, speed):
    desired = target.sub(enemy.position)
    l = desired.length()
    if l == 0:
        return Vector2()
    return desired.normalized().mul(speed)


def segment_hits_circle(a, b, center, radius):
    ab = b.sub(a)
    ab_len_sq = ab.x * ab.x + ab.y * ab.y
    if ab_len_sq == 0:
        return center.sub(a).length() <= radius
    t = max(0, min(1, (center.sub(a).x * ab.x + center.sub(a).y * ab.y) / ab_len_sq))
    closest = Vector2(a.x + ab.x * t, a.y + ab.y * t)
    return center.sub(closest).length() <= radius


def line_blocked_by_obstacles(enemy, player_pos, obstacles):
    for ob in obstacles:
        if segment_hits_circle(player_pos, enemy.position, ob.collider.position, ob.collider.radius):
            return True
    return False


def visible_to_player(enemy, player, obstacles):
    return not line_blocked_by_obstacles(enemy, player.position, obstacles)


def flee_from_player(enemy, player, max_distance=400):   
    away = enemy.position.sub(player.position)
    dist = away.length()
    
    if dist >= max_distance:
        return Vector2()

    return away.normalized().mul(enemy.attack_speed)



def hide_from_player(enemy, player, obstacles):
    best_spot = None
    best_dist = None
    player_pos = player.position

    for ob in obstacles:
        to_ob = ob.collider.position.sub(player_pos)
        if to_ob.length() == 0:
            continue
        spot_dir = to_ob.normalized()
        hide_offset = ob.collider.radius + enemy.collider.radius + enemy.hide_distance
        spot = ob.collider.position.add(spot_dir.mul(hide_offset))
        dist = spot.sub(enemy.position).length()

        if best_spot is None or dist < best_dist:
            best_spot = spot
            best_dist = dist

    if best_spot:
        return seek(enemy, best_spot, enemy.max_speed)

    away = enemy.position.sub(player_pos)
    if away.length() == 0:
        return Vector2()
    return away.normalized().mul(enemy.max_speed)


def avoid_obstacles(enemy, obstacles, width, height):
    steer = Vector2()
    r = enemy.collider.radius

    head = heading(enemy)
    look_ahead = r + max(enemy.max_speed, enemy.attack_speed) * 0.4

    for ob in obstacles:
        to_ob = ob.collider.position.sub(enemy.position)
        proj = to_ob.x * head.x + to_ob.y * head.y
        if proj < 0 or proj > look_ahead:
            continue

        perp = abs(to_ob.x * (-head.y) + to_ob.y * head.x)
        min_clear = r + ob.collider.radius + 10
        if perp < min_clear:
            away = enemy.position.sub(ob.collider.position).normalized().mul((min_clear - perp))
            steer = steer.add(away)

        dist = to_ob.length()
        if 0 < dist < min_clear:
            push = to_ob.normalized().mul(min_clear - dist)
            steer = steer.add(push)

    wall_margin = r + 25
    if enemy.position.x < wall_margin:
        steer.x += (wall_margin - enemy.position.x)
    elif enemy.position.x > width - wall_margin:
        steer.x -= (enemy.position.x - (width - wall_margin))

    if enemy.position.y < wall_margin:
        steer.y += (wall_margin - enemy.position.y)
    elif enemy.position.y > height - wall_margin:
        steer.y -= (enemy.position.y - (height - wall_margin))

    return steer.mul(enemy.avoid_weight)


def separate(enemy, enemies):
    steer = Vector2()
    for other in enemies:
        if other is enemy:
            continue
        diff = enemy.position.sub(other.position)
        dist = diff.length()
        min_dist = enemy.collider.radius + other.collider.radius + 12
        if 0 < dist < min_dist:
            steer = steer.add(diff.normalized().mul((min_dist - dist)))
    return steer.mul(enemy.separation_weight)


def cohesion(enemy, enemies, radius=200):
    center = Vector2()
    count = 0
    for other in enemies:
        if other is enemy:
            continue
        dist = enemy.position.sub(other.position).length()
        if dist <= radius:
            center = center.add(other.position)
            count += 1
    if count == 0:
        return Vector2()
    center = center.mul(1.0 / count)
    return seek(enemy, center, enemy.max_speed)


def center_bias(enemy, width, height, strength):
    to_center = Vector2(width * 0.5 - enemy.position.x, height * 0.5 - enemy.position.y)
    if to_center.length() == 0:
        return Vector2()
    return to_center.normalized().mul(strength)


def roam_core(enemy, dt, enemies, obstacles, width, height):
    wander_force = wander(enemy, dt)
    avoid_force = avoid_obstacles(enemy, obstacles, width, height)
    coh = cohesion(enemy, enemies, radius=180).mul(0.2)
    sep = separate(enemy, enemies)
    avoid_multiplier = 1.2 + (0.3 if enemy.is_bold else 0.0)
    desired = Vector2()
    desired = desired.add(avoid_force.mul(avoid_multiplier))
    desired = desired.add(coh)
    desired = desired.add(sep)
    wander_scale = 0.5 if avoid_force.length() > 5 else 1.0
    desired = desired.add(wander_force.mul(wander_scale))
    desired = desired.add(center_bias(enemy, width, height, enemy.max_speed * 0.25))
    return desired, wander_force


def random_jitter(enemy):
    return random.uniform(-enemy.wander_jitter, enemy.wander_jitter)


def steer_attack(enemy, player, enemies, obstacles, width, height):
    desired = Vector2()
    desired = desired.add(seek(enemy, player.position, enemy.attack_speed))
    desired = desired.add(separate(enemy, enemies))
    desired = desired.add(avoid_obstacles(enemy, obstacles, width, height))
    return desired, enemy.attack_speed


def steer_hide(enemy, dt, player, enemies, obstacles, width, height):
    desired, wander_force = roam_core(enemy, dt, enemies, obstacles, width, height)
    visible = visible_to_player(enemy, player, obstacles)

    if visible and not enemy.is_bold:
        desired = desired.add(flee_from_player(enemy, player).mul(enemy.los_flee_weight))
        desired = desired.add(hide_from_player(enemy, player, obstacles).mul(enemy.hide_weight))
        desired = desired.add(wander_force.mul(0.6))
        max_speed = enemy.attack_speed
    else:
        if enemy.is_bold:
            desired = desired.add(heading(enemy).mul(enemy.max_speed * 0.5))
            max_speed = enemy.attack_speed
        else:
            max_speed = enemy.max_speed
    return desired, max_speed
