import pygame
from entities.player import Player
from entities.obstacle import Obstacle
from systems.map_boundary import resolve_map_collision
from systems.collisions import resolve_player_obstacle_collision

def main():
    pygame.init()

    WIDTH, HEIGHT = 1200, 800
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    player = Player(WIDTH // 2, HEIGHT // 2)

    obstacles = [
        Obstacle(300, 300, 60),
        Obstacle(800, 500, 80),
        Obstacle(600, 200, 40)
    ]

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        player.update(dt, keys, mouse_pos)

        resolve_map_collision(player, WIDTH, HEIGHT)

        for ob in obstacles:
            resolve_player_obstacle_collision(player, ob)

        screen.fill((25, 25, 30))

        for ob in obstacles:
            ob.draw(screen)

        player.draw(screen)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
