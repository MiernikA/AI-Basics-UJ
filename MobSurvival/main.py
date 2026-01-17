import pygame

from entities.obstacle import Obstacle
from entities.player import Player
from systems.enemy_manager import spawn_enemies, trigger_attack_clusters

from systems.map_boundary import resolve_map_collision
from systems.collisions import resolve_player_obstacle_collision, resolve_player_enemy_collision
from systems.railgun import Railgun


def main():
    pygame.init()

    WIDTH, HEIGHT = 1200, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    obstacles = [
        Obstacle(300, 300, 60),
        Obstacle(800, 500, 80),
        Obstacle(600, 200, 40),
        Obstacle(950, 200, 25),
    ]

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
            enemy.draw(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
