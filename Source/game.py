import numpy as np
from random import shuffle
import pygame

TILE_SIZE = 60


class Tile(pygame.sprite.Sprite):
    def __init__(self, type, grid_x, grid_y):
        # Call the parent's constructor
        pygame.sprite.Sprite.__init__(self)
        # load image based on tile type
        filename = None
        if type == 0:
            filename = "Assets/Images/Star_Back.png"
        elif type == 1:
            filename = "Assets/Images/Star_Wall.png"
        self.image = pygame.image.load(filename).convert()
        # move tile to the proper location on the grid
        self.rect = self.image.get_rect()
        self.rect.top = TILE_SIZE * grid_y
        self.rect.left = TILE_SIZE * grid_x

class Level:
    # width, height should be odd
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.player_spawn_point = (height//2, width//2)
        self.tile_map = None
        self.generate_tile_map()

    # generates a tile map in-place
    def generate_tile_map(self):
        width, height = self.width, self.height
        tile_map = np.zeros((height, width), dtype=int)
        # surround map with unpassable wall border
        for x in range(width):
            tile_map[0, x] = 1
            tile_map[-1, x] = 1
        for y in range(height):
            tile_map[y, 0] = 1
            tile_map[y, -1] = 1
        # generate pillars
        for x in range(0, width, 2):
            for y in range(0, height, 2):
                tile_map[y, x] = 1
        # save map
        self.tile_map = tile_map
        # fill with walls randomly
        self.add_random_walls()
        # make a hole for a spawn point
        self.poke_hole_in_tile_map(tile_map, self.player_spawn_point[1],
                                   self.player_spawn_point[0], 1)

    def poke_hole_in_tile_map(self, tile_map, location_x, location_y, radius):
        for x in range(-radius, radius+1):
            for y in range(-radius, radius+1):
                tile_map[location_y + y, location_x + x] = 0

    # add walls to the maze, making sure that there is always a path between 2 points
    def add_random_walls(self, chance=0.5):
        # create list of points
        points = []
        for x in range(2, self.width-1, 2):
            for y in range(1, self.height-1, 2):
                points.append((y, x))
        for x in range(1, self.width-1, 2):
            for y in range(2, self.height-1, 2):
                points.append((y, x))
        shuffle(points)
        for y, x in points:
            # add wall if it doesn't obstruct movement
            if self.can_place_wall(y, x):
                if np.random.random_sample() < chance:  # not always
                    self.tile_map[y, x] = 1

    # a wall can be placed if it doesn't block passage between any 2 points in the maze
    def can_place_wall(self, wall_y, wall_x):
        if self.tile_map[wall_y, wall_x] == 1:  # wall is already there
            return True
        self.tile_map[wall_y, wall_x] = 1  # imagine there is a wall
        get_adjacent = lambda y, x: [(y, x+1), (y, x-1), (y-1, x), (y+1, x)]  # right, left, up, down
        # BFS search from any of the adjacent empty tiles
        visited = np.zeros(self.tile_map.shape, dtype=int)
        tile_y, tile_x = None, None
        for t_y, t_x in get_adjacent(wall_y, wall_x): # find first adjacent empty cell
            if self.tile_map[t_y, t_x] == 0:
                tile_y, tile_x = t_y, t_x
                break
        visited[tile_y, tile_x] = 1
        queue = [(tile_y, tile_x)]
        while queue:
            y, x = queue.pop(0)
            directions = get_adjacent(y, x)
            for dir_y, dir_x in directions:
                if not visited[dir_y, dir_x] and self.tile_map[dir_y, dir_x] == 0:
                    visited[dir_y, dir_x] = 1
                    queue.append((dir_y, dir_x))
        # if any empty tile on the map wasn't visited by BFS, then the wall prevents passage
        answer = True
        for x in range(self.width):
            for y in range(self.height):
                if self.tile_map[y, x] == 0 and not visited[y, x]:
                    answer = False
                    break
        self.tile_map[wall_y, wall_x] = 0  # remove the hypothetical wall
        return answer

    # get a list of sprites for rendering
    def set_up_tile_sprites(self):
        tile_list = pygame.sprite.RenderPlain()
        for x in range(self.width):
            for y in range(self.height):
                tile_type = self.tile_map[y, x]
                tile_list.add(Tile(tile_type, x, y))
        return tile_list

class PacMan:
    def __init__(self):
        pass