import pygame

from src.core.config import (
    COLOR_BG,
    DEBUG_DRAW_NAV,
    DEBUG_DRAW_PATHS,
    DEBUG_DRAW_STATE,
    FONT_NAME,
    FONT_SIZE,
    FPS,
    WINDOW_SIZE,
)
from src.game.world import World


def main() -> int:
    pygame.init()
    pygame.display.set_caption("Bot Shooter - Project 2")
    screen = pygame.display.set_mode(WINDOW_SIZE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(FONT_NAME, FONT_SIZE)
    font_bold = pygame.font.SysFont(FONT_NAME, FONT_SIZE, bold=True)

    world = World()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        world.update(dt)

        screen.fill(COLOR_BG)
        world.draw(screen, font)
        if DEBUG_DRAW_NAV:
            world.draw_debug(screen)
        if DEBUG_DRAW_STATE:
            draw_hud(screen, font, font_bold, world)
        pygame.display.flip()

    pygame.quit()
    return 0


def draw_hud(
    screen: pygame.Surface,
    font: pygame.font.Font,
    font_bold: pygame.font.Font,
    world: World,
) -> None:
    x, y = 12, 12
    padding = 10
    rows = []
    for bot in world.bots:
        status = "waiting for respawn" if bot.health <= 0 else bot.state
        rows.append(
            [
                ("Bot", f"{bot.bot_id}", font, font_bold),
                ("HP", f"{bot.health}", font, font_bold),
                ("Ray ammo", f"{bot.ammo_rail}", font, font_bold),
                ("Rocket ammo", f"{bot.ammo_rocket}", font, font_bold),
                ("Kills", f"{bot.kills}", font, font_bold),
                ("Behavior", status, font, font_bold),
            ]
        )

    col_widths = [0] * len(rows[0]) if rows else []
    for row in rows:
        for idx, (label_text, value_text, label_font, value_font) in enumerate(row):
            label_surf = label_font.render(label_text, True, (210, 220, 230))
            value_surf = value_font.render(value_text, True, (240, 240, 255))
            col_widths[idx] = max(col_widths[idx], label_surf.get_width() + 6 + value_surf.get_width())

    col_x = []
    cursor_x = x
    for width in col_widths:
        col_x.append(cursor_x)
        cursor_x += width + padding

    for row in rows:
        for idx, (label_text, value_text, label_font, value_font) in enumerate(row):
            base_x = col_x[idx]
            label = label_font.render(label_text, True, (210, 220, 230))
            screen.blit(label, (base_x, y))
            value = value_font.render(value_text, True, (240, 240, 255))
            screen.blit(value, (base_x + label.get_width() + 6, y))
        y += 18


if __name__ == "__main__":
    raise SystemExit(main())
