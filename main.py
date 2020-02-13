# import the pygame module, so you can use it
import pygame
import Source.game as game

LEVEL_WIDTH = 19
LEVEL_HEIGHT = 11


# define a main function
def main():
    # initialize the pygame module
    pygame.init()
    # load and set the logo
    logo = pygame.image.load("Assets/Images/unicorn-logo.png")
    pygame.display.set_icon(logo)
    pygame.display.set_caption("PacMan of Kthulhu")

    # create a surface on screen that fits the size of the map
    screen = pygame.display.set_mode((LEVEL_WIDTH*game.TILE_SIZE,
                                      LEVEL_HEIGHT*game.TILE_SIZE))

    # create level
    level = game.Level(LEVEL_WIDTH, LEVEL_HEIGHT)
    # get tile sprites
    tile_list = level.set_up_tile_sprites()
    pacman = game.PacMan(LEVEL_WIDTH // 2, LEVEL_HEIGHT // 2)
    # create lists of all game objects
    characters_list = pygame.sprite.RenderPlain()
    characters_list.add(pacman)
    objects_list = pygame.sprite.RenderPlain()

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
            # place coins on mouse clicks
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                tile_x, tile_y = mouse_x // game.TILE_SIZE, mouse_y // game.TILE_SIZE
                if level.tile_map[tile_y, tile_x] == 0:  # only place coins in empty corridors
                    coin = game.Coin(tile_x, tile_y)
                    objects_list.add(coin)
                # clicked_tiles = [s for s in tile_list if s.rect.collidepoint(mouse_pos)]

        # update game logic
        objects_list.update()

        # draw everything
        tile_list.draw(screen)
        characters_list.draw(screen)
        objects_list.draw(screen)
        pygame.display.flip()
        clock.tick(60)

# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__ == "__main__":
    # call the main function
    main()
