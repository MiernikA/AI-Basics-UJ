def resolve_map_collision(player, width, height):
    r = player.collider.radius

    if player.position.x - r < 0:
        player.position.x = r
    if player.position.x + r > width:
        player.position.x = width - r

    if player.position.y - r < 0:
        player.position.y = r
    if player.position.y + r > height:
        player.position.y = height - r

    player.collider.position = player.position