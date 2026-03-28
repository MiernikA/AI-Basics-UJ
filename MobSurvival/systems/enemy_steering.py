import math

from core.vector2 import Vector2


def heading(enemy):
    if enemy.velocity.length() == 0:
        return Vector2(1, 0)
    return enemy.velocity.normalized()


def side(enemy):
    return heading(enemy).perp()


def seek(enemy, target, speed):
    desired = target.sub(enemy.position)
    l = desired.length()
    if l == 0:
        return Vector2()
    desired_velocity = desired.normalized().mul(speed)
    return desired_velocity.sub(enemy.velocity)


def player_forward(player):
    return Vector2(math.cos(player.angle), math.sin(player.angle))


def escape_shoot_line(enemy, player):
    forward = player_forward(player)
    to_enemy = enemy.position.sub(player.position)
    along = to_enemy.dot(forward)
    if along <= 0:
        enemy.debug_target = None
        return Vector2()

    lateral = to_enemy.dot(forward.perp())
    corridor = enemy.group_range * 0.45
    abs_lateral = abs(lateral)
    if abs_lateral >= corridor:
        enemy.debug_target = None
        return Vector2()

    lateral_sign = -1 if lateral < 0 else 1
    side_step = forward.perp().mul(lateral_sign)
    escape_distance = corridor - abs_lateral + enemy.collider.radius * 6.0
    target = enemy.position.add(side_step.mul(escape_distance))
    enemy.debug_target = target
    return seek(enemy, target, enemy.attack_speed)


def group_up_with_allies(enemy, enemies):
    nearby = []
    nearest = None
    nearest_dist = None

    for other in enemies:
        if other is enemy or other.state == "attack":
            continue
        dist = enemy.position.sub(other.position).length()
        if dist <= enemy.group_range:
            nearby.append(other)
        if nearest is None or dist < nearest_dist:
            nearest = other
            nearest_dist = dist

    if nearby:
        center = enemy.position
        for other in nearby:
            center = center.add(other.position)
        center = center.mul(1.0 / (len(nearby) + 1))
        enemy.debug_target = center
        return seek(enemy, center, enemy.attack_speed), max(enemy.attack_speed, enemy.max_speed * 1.05)

    if nearest is not None:
        enemy.debug_target = nearest.position
        return seek(enemy, nearest.position, enemy.attack_speed), max(enemy.attack_speed, enemy.max_speed * 1.05)

    enemy.debug_target = None
    return Vector2(), enemy.max_speed


def avoid_obstacles(enemy, obstacles, width, height):
    steer = Vector2()
    r = enemy.collider.radius

    head = heading(enemy)
    side_vec = side(enemy)
    speed_ratio = enemy.velocity.length() / max(enemy.max_speed, 1)
    look_ahead = enemy.min_detection_box + (enemy.detection_box_scale * speed_ratio)

    for ob in obstacles:
        local = ob.collider.position.sub(enemy.position)
        local_x = local.dot(head)
        local_y = local.dot(side_vec)
        expanded = ob.collider.radius + r

        if local_x < 0 or local_x > look_ahead:
            continue

        if abs(local_y) >= expanded:
            continue

        multiplier = 1.0 + (look_ahead - local_x) / max(look_ahead, 1.0)
        lateral = side_vec.mul((-local_y / max(expanded, 1.0)) * enemy.max_force * multiplier)
        braking = head.mul(-enemy.brake_weight * max(expanded - local_x, 0.0))
        steer = steer.add(lateral).add(braking)

    wall_margin = r + 25
    if enemy.position.x < wall_margin:
        steer.x += (wall_margin - enemy.position.x) * enemy.max_force
    elif enemy.position.x > width - wall_margin:
        steer.x -= (enemy.position.x - (width - wall_margin)) * enemy.max_force

    if enemy.position.y < wall_margin:
        steer.y += (wall_margin - enemy.position.y) * enemy.max_force
    elif enemy.position.y > height - wall_margin:
        steer.y -= (enemy.position.y - (height - wall_margin)) * enemy.max_force

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
            steer = steer.add(diff.normalized().mul((min_dist - dist) / dist))
    return steer.mul(enemy.separation_weight)


def steer_attack(enemy, player, enemies, obstacles, width, height):
    enemy.debug_target = player.position
    desired = Vector2()
    desired = desired.add(seek(enemy, player.position, enemy.attack_speed))
    desired = desired.add(separate(enemy, enemies))
    desired = desired.add(avoid_obstacles(enemy, obstacles, width, height))
    return desired, enemy.attack_speed


def steer_bold(enemy, player, enemies, obstacles, width, height):
    desired, max_speed = group_up_with_allies(enemy, enemies)
    desired = desired.add(separate(enemy, enemies))
    desired = desired.add(avoid_obstacles(enemy, obstacles, width, height))

    attack_pull = seek(enemy, player.position, enemy.max_speed * 0.35)
    desired = desired.add(attack_pull)
    return desired, max_speed


def steer_hide(enemy, dt, player, enemies, obstacles, width, height):
    enemy.debug_target = None
    desired = Vector2()
    desired = desired.add(escape_shoot_line(enemy, player).mul(enemy.los_flee_weight * 2.0))
    desired = desired.add(separate(enemy, enemies))
    desired = desired.add(avoid_obstacles(enemy, obstacles, width, height))
    max_speed = enemy.attack_speed
    return desired, max_speed
