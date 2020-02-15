import os
import pygame
import pygame.freetype
import Source.game as game

LEVEL_WIDTH = 19
LEVEL_HEIGHT = 11
# GAME_MODE = "Pathfinding"
GAME_MODE = "Game"


def draw_score(screen, score):
    score_string = "SCORE:" + str(score).zfill(4)
    font = pygame.freetype.Font("Assets/Fonts/PokemonGb.ttf", 32)
    text, text_rect = font.render(score_string, (255, 255, 255))
    text_rect.top = 14
    text_rect.left = 14
    screen.blit(text, text_rect)

# define a main function
def main():
    # move window to upper left corner
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 32)
    # initialize the pygame module
    pygame.init()
    pygame.font.init()
    # load and set the logo
    logo = pygame.image.load("Assets/Images/unicorn-logo.png")
    pygame.display.set_icon(logo)
    pygame.display.set_caption("PacMan of Kthulhu")

    # create a surface on screen that fits the size of the map
    screen = pygame.display.set_mode((LEVEL_WIDTH*game.TILE_SIZE,
                                      LEVEL_HEIGHT*game.TILE_SIZE))

    # create level
    level = None
    if GAME_MODE == "Pathfinding":
        level = game.Level(LEVEL_WIDTH, LEVEL_HEIGHT, difficulty=0, ghosts_n_coins=False)
    elif GAME_MODE == "Game":
        level = game.Level(LEVEL_WIDTH, LEVEL_HEIGHT, difficulty=0, ghosts_n_coins=True)
    # get tile sprites
    tile_list = level.set_up_tile_sprites()
    # create pacman
    pacman = game.PacMan(LEVEL_WIDTH // 2, LEVEL_HEIGHT // 2)
    pacman_list = pygame.sprite.RenderPlain()
    pacman_list.add(pacman)

    # game clock
    clock = pygame.time.Clock()

    # define a variable to control the main loop
    running = True

    # main loop
    while running:
        # event handling, gets all event from the event queue
        for event in pygame.event.get():
            # only do something if the event is of type QUIT
            if event.type == pygame.QUIT:
                # change the value to False, to exit the main loop
                running = False
            # place coins on mouse clicks (only in pathfinding mode)
            elif event.type == pygame.MOUSEBUTTONDOWN and GAME_MODE == "Pathfinding":
                mouse_x, mouse_y = pygame.mouse.get_pos()
                tile_x, tile_y = mouse_x // game.TILE_SIZE, mouse_y // game.TILE_SIZE
                if level.tile_map[tile_y, tile_x] == 0:  # only place coins in empty corridors
                    level.add_coin(tile_x, tile_y)
                # clicked_tiles = [s for s in tile_list if s.rect.collidepoint(mouse_pos)]

        # update game logic
        pacman.update(level)
        level.ghosts.update(level, pacman)
        level.update()

        # draw everything
        tile_list.draw(screen)
        level.coins.draw(screen)
        pacman_list.draw(screen)
        level.ghosts.draw(screen)
        draw_score(screen, level.score)
        pygame.display.flip()
        clock.tick(60)


# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__ == "__main__":
    # call the main function
    main()
