import random

import pygame

from entities.obstacle import Obstacle
from entities.player import Player
from systems.enemy_manager import spawn_enemies, trigger_attack_clusters
from systems.enemy_manager import CLUSTER_RADIUS

from systems.map_boundary import resolve_map_collision
from systems.collisions import resolve_player_obstacle_collision, resolve_player_enemy_collision
from systems.railgun import Railgun


def generate_obstacles(width, height, min_count=4, max_count=4, max_attempts=40):
    obstacles = []
    center = pygame.Vector2(width * 0.5, height * 0.5)
    player_safe_radius = 170
    count = random.randint(min_count, max_count)

    for _ in range(count):
        for _attempt in range(max_attempts):
            radius = random.randint(25, 95)
            x = random.randint(radius + 20, width - radius - 20)
            y = random.randint(radius + 20, height - radius - 20)
            pos = pygame.Vector2(x, y)

            if pos.distance_to(center) < player_safe_radius + radius:
                continue

            overlaps = False
            for obstacle in obstacles:
                obstacle_pos = pygame.Vector2(obstacle.collider.position.x, obstacle.collider.position.y)
                min_dist = obstacle.collider.radius + radius + 30
                if pos.distance_to(obstacle_pos) < min_dist:
                    overlaps = True
                    break

            if not overlaps:
                obstacles.append(Obstacle(x, y, radius))
                break

    if not obstacles:
        obstacles.append(Obstacle(width // 4, height // 3, 55))

    return obstacles


def draw_legend(screen, font):
    entries = [
        ("Hide", (80, 220, 120)),
        ("Bold", (255, 210, 70)),
        ("Attack", (255, 70, 70)),
    ]
    panel = pygame.Rect(16, 16, 214, 160)
    pygame.draw.rect(screen, (12, 12, 18), panel, border_radius=10)
    pygame.draw.rect(screen, (90, 90, 110), panel, 2, border_radius=10)

    title = font.render("Mob States", True, (230, 230, 235))
    screen.blit(title, (panel.x + 20, panel.y + 16))

    for index, (label, color) in enumerate(entries):
        y = panel.y + 46 + index * 18
        pygame.draw.circle(screen, color, (panel.x + 24, y + 7), 5)
        text = font.render(label, True, (220, 220, 225))
        screen.blit(text, (panel.x + 38, y))

    info_lines = [
        "Ring: group range",
        "State line: heading",
        "Blue line: target",
    ]
    for index, label in enumerate(info_lines):
        y = panel.y + 104 + index * 13
        text = font.render(label, True, (180, 190, 205))
        screen.blit(text, (panel.x + 20, y))


def main():
    pygame.init()

    WIDTH, HEIGHT = 1200, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 19)

    obstacles = generate_obstacles(WIDTH, HEIGHT)

    player = Player(WIDTH // 2, HEIGHT // 2)
    enemies = spawn_enemies(14, WIDTH, HEIGHT, obstacles)
    railgun = Railgun()

    running = True
    space_was_down = False
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        player.update(dt, keys, mouse_pos)
        railgun.update(dt)
        for enemy in enemies:
            enemy.update(dt, WIDTH, HEIGHT, obstacles, enemies, player)
        if len(enemies) <= 4:
            for e in enemies:
                e.state = "attack"
                e.cluster_id = -1
        else:
            trigger_attack_clusters(enemies)
        space_down = keys[pygame.K_SPACE]

        resolve_map_collision(player, WIDTH, HEIGHT)
        for enemy in enemies:
            if resolve_player_enemy_collision(player, enemy):
                print("GAME OVER")
                running = False

        for ob in obstacles:
            resolve_player_obstacle_collision(player, ob)
        
        if space_down and not space_was_down and player.can_shoot():
            killed = railgun.fire(player, enemies, obstacles)
            for e in killed:
                enemies.remove(e)
            player.trigger_shot_cooldown(0.7)

        space_was_down = space_down

        if len(enemies) == 0:
            print("YOU WIN")
            running = False

        screen.fill((25, 25, 30))

        for ob in obstacles:
            ob.draw(screen)

        player.draw(screen)
        railgun.draw(screen)

        for enemy in enemies:
            enemy.draw_debug(screen, CLUSTER_RADIUS + 30)
        for enemy in enemies:
            enemy.draw(screen)

        draw_legend(screen, font)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
