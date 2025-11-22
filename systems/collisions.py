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
