def resolve_player_obstacle_collision(player, obstacle):
    p = player.collider.position
    o = obstacle.collider.position

    diff = p.sub(o)
    dist = diff.length()
    min_dist = player.collider.radius + obstacle.collider.radius

    if dist < min_dist:
        push = diff.normalized().mul(min_dist - dist)
        player.position = player.position.add(push)
        player.collider.position = player.position

def resolve_player_enemy_collision(player, enemy):
    p = player.collider.position
    e = enemy.collider.position

    diff = p.sub(e)
    dist = diff.length()
    min_dist = player.collider.radius + enemy.collider.radius

    return dist < min_dist

