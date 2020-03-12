import os
import pygame
import pygame.freetype
import sympy
import Source.game as game
from datetime import datetime
from datetime import timedelta

LEVEL_WIDTH = 9
LEVEL_HEIGHT = 9
# GAME_MODE = "Pathfinding"
GAME_MODE = "Game"


def draw_score(screen, score):
    score_string = "SCORE:" + str(score).zfill(4)
    font = pygame.freetype.Font("Assets/Fonts/PokemonGb.ttf", 32)
    text, text_rect = font.render(score_string, (255, 255, 255))
    text_rect.top = 14
    text_rect.left = 14
    screen.blit(text, text_rect)


def draw_floating_label(screen, animation_progress, string, color, font_size):
    height, width = pygame.display.get_surface().get_size()
    font = pygame.freetype.Font("Assets/Fonts/PokemonGb.ttf", font_size)
    text, text_rect = font.render(string, color)
    y = -int(sympy.cot(0.001+animation_progress*3.15)*40) + height // 2
    text_rect.center = width // 2, y
    screen.blit(text, text_rect)


def draw_pathfinding_stats(screen, stats):
    font = pygame.freetype.Font("Assets/Fonts/PokemonGb.ttf", 16)
    time = datetime.min + stats['time']
    color = (255, 255, 255)
    algo_str = f"Algorithm: {stats['algo']}"
    text, text_rect = font.render(algo_str, color)
    text_rect.left = 0
    text_rect.top = 55
    screen.blit(text, text_rect)
    time_str = f"Time (ss.mcs) {time.strftime('%S.%f')}"
    text, text_rect = font.render(time_str, color)
    text_rect.left = 0
    text_rect.top = 80
    screen.blit(text, text_rect)
    steps_str = f"Steps: {stats['steps']}"
    text, text_rect = font.render(steps_str, color)
    text_rect.left = 0
    text_rect.top = 105
    screen.blit(text, text_rect)
    memory_str = f"Memory: {stats['memory']} Bytes"
    text, text_rect = font.render(memory_str, color)
    text_rect.left = 0
    text_rect.top = 130
    screen.blit(text, text_rect)


def create_level(difficulty):
    level = None
    if GAME_MODE == "Pathfinding":
        level = game.Level(LEVEL_WIDTH, LEVEL_HEIGHT, difficulty=0, ghosts_n_coins=False)
    elif GAME_MODE == "Game":
        level = game.Level(LEVEL_WIDTH, LEVEL_HEIGHT, difficulty=difficulty, ghosts_n_coins=True)
    # get tile sprites
    tile_list = level.set_up_tile_sprites()
    # create pacman
    pacman = game.PacMan(LEVEL_WIDTH // 2, LEVEL_HEIGHT // 2)
    pacman_list = pygame.sprite.RenderPlain()
    pacman_list.add(pacman)
    return level, pacman, pacman_list, tile_list


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

    game_state = "running"
    current_difficulty = 0

    # "victory" and "defeat" labels
    floating_text_animation_frame = 0
    floating_text_animation_frames = 120

    # create level
    level, pacman, pacman_list, tile_list = create_level(current_difficulty)
    pathfinding_stats = {"algo": "bfs", "time": timedelta(microseconds=0),
                         "steps": 0, "memory": 0}  # stats about pathfinding algorithms

    # game clock
    clock = pygame.time.Clock()

    # define a variable to control the main loop
    running = True
    # pause the game with space
    pause = False

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
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                pause = not pause  # pause/unpause
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                level.toggle_pathfinding_algo()  # switch to next pathfinding algorithm

        # update game logic
        if not pause:
            if game_state == "running":
                pacman.update(level, GAME_MODE, pathfinding_stats)
                level.ghosts.update(level, pacman)
                level.update()
                if not level.coins and GAME_MODE == "Game":  # win the game once all of the coins have been eaten
                    game_state = "victory"
                    current_difficulty += 1  # bump up the difficulty
                elif pacman.dead:
                    game_state = "defeat"
                    current_difficulty = 0  # reset difficulty
            elif game_state == "victory":
                pass
                # update victorious animation
                floating_text_animation_frame += 1
                # create next level
                if floating_text_animation_frame >= floating_text_animation_frames:
                    floating_text_animation_frame = 0
                    curr_score = level.score  # maintain score
                    level, pacman, pacman_list, tile_list = create_level(current_difficulty)
                    level.score = curr_score
                    game_state = "running"
            elif game_state == "defeat":
                pass
                # update defeat animation
                floating_text_animation_frame += 1
                # create next level
                if floating_text_animation_frame >= floating_text_animation_frames:
                    floating_text_animation_frame = 0
                    level, pacman, pacman_list, tile_list = create_level(current_difficulty)
                    game_state = "running"

        # draw everything
        tile_list.draw(screen)
        level.coins.draw(screen)
        pacman_list.draw(screen)
        level.ghosts.draw(screen)
        draw_score(screen, level.score)
        if GAME_MODE == "Pathfinding":
            draw_pathfinding_stats(screen, pathfinding_stats)
        animation_progress = floating_text_animation_frame / floating_text_animation_frames
        if game_state == "victory":
            label_text = f"Onwards to level {current_difficulty}!"
            draw_floating_label(screen, animation_progress, label_text, (255, 248, 99), 24)
        elif game_state == "defeat":
            draw_floating_label(screen, animation_progress, "DEAD", (209, 0, 28), 64)
        pygame.display.flip()
        clock.tick(60)


# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__ == "__main__":
    # call the main function
    main()
