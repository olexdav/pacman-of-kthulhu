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
        # draw everything
        screen.fill((0, 0, 0))  # fill with black
        tile_list.draw(screen)
        pygame.display.flip()
        clock.tick(30)

# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__ == "__main__":
    # call the main function
    main()
