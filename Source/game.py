import os
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
        self.player_spawn_point = (height // 2, width // 2)
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
        for x in range(-radius, radius + 1):
            for y in range(-radius, radius + 1):
                tile_map[location_y + y, location_x + x] = 0

    # add walls to the maze, making sure that there is always a path between 2 points
    def add_random_walls(self, chance=0.5):
        # create list of points
        points = []
        for x in range(2, self.width - 1, 2):
            for y in range(1, self.height - 1, 2):
                points.append((y, x))
        for x in range(1, self.width - 1, 2):
            for y in range(2, self.height - 1, 2):
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
        get_adjacent = lambda y, x: [(y, x + 1), (y, x - 1), (y - 1, x), (y + 1, x)]  # right, left, up, down
        # BFS search from any of the adjacent empty tiles
        visited = np.zeros(self.tile_map.shape, dtype=int)
        tile_y, tile_x = None, None
        for t_y, t_x in get_adjacent(wall_y, wall_x):  # find first adjacent empty cell
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

    # find shortest path between two points and return a sequence of moves
    def find_shortest_path(self, x1, y1, x2, y2):
        return self.shortest_path_bfs(x1, y1, x2, y2)

    # return moves that need to be taken to reach a point based on a distance matrix
    @staticmethod
    def moves_from_distance_matrix(x1, y1, x2, y2, dist_mat):
        curr_x, curr_y = x2, y2
        moves = []
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]  # right, left, up, down
        while curr_x != x1 or curr_y != y1:
            dist = dist_mat[curr_y, curr_x]
            # check all directions
            for dir in directions:
                dir_dist = dist_mat[curr_y - dir[0], curr_x - dir[1]]
                if dir_dist == dist-1:  # move is optimal
                    moves.append(dir)
                    curr_y -= dir[0]
                    curr_x -= dir[1]
                    break
        moves.reverse()
        return moves

    def shortest_path_bfs(self, x1, y1, x2, y2):
        get_adjacent = lambda y, x: [(y, x + 1), (y, x - 1), (y - 1, x), (y + 1, x)]  # right, left, up, down
        distance_matrix = np.ones(self.tile_map.shape, dtype=int) * -1
        # fill distance matrix
        distance_matrix[y1, x1] = 0
        queue = [(y1, x1)]
        while queue:
            y, x = queue.pop(0)
            directions = get_adjacent(y, x)
            for dir_y, dir_x in directions:
                if self.tile_map[dir_y, dir_x] == 0:
                    dist = distance_matrix[y, x] + 1
                    if distance_matrix[dir_y, dir_x] == -1 or dist < distance_matrix[dir_y, dir_x]:
                        distance_matrix[dir_y, dir_x] = dist
                        queue.append((dir_y, dir_x))
        return Level.moves_from_distance_matrix(x1, y1, x2, y2, distance_matrix)

    def shortest_path_a_star(self, x1, y1, x2, y2):
        pass


class PacMan(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y):
        # Call the parent's constructor
        pygame.sprite.Sprite.__init__(self)
        # load image
        self.image = pygame.image.load("Assets/Images/pacman.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.left = tile_x * TILE_SIZE
        self.rect.top = tile_y * TILE_SIZE
        # movement
        self.curr_tile_x, self.curr_tile_y = tile_x, tile_y
        self.move_frames = 20  # how many frames it takes to move one cell
        self.move_frame = 0
        self.curr_move = None  # current direction of movement
        self.planned_moves = []

    def update(self, level, coins):
        # fetch a move from the queue
        if not self.curr_move:
            if self.planned_moves:
                self.curr_move = self.planned_moves.pop(0)
                self.move_frame = 0
        # update position based on movement
        if self.curr_move:
            self.move_frame += 1
            movement_percent = self.move_frame / self.move_frames
            self.rect.left = int((self.curr_tile_x + self.curr_move[1] * movement_percent) * TILE_SIZE)
            self.rect.top = int((self.curr_tile_y + self.curr_move[0] * movement_percent) * TILE_SIZE)
            if self.move_frame >= self.move_frames:  # finish move
                self.curr_tile_x += self.curr_move[1]
                self.curr_tile_y += self.curr_move[0]
                self.curr_move = None
        # movement finished: search for new targets
        if not self.curr_move and not self.planned_moves and coins:
            for coin in coins:
                # if pacman is on top of the coin, consume it immediately
                if self.curr_tile_x == coin.tile_x and self.curr_tile_y == coin.tile_y:
                    coin.kill()  # devour the coin
                else:  # try to reach the coin
                    self.planned_moves = level.find_shortest_path(self.curr_tile_x, self.curr_tile_y,
                                                                  coin.tile_x, coin.tile_y)
                    break  # only try to eat the first coin on the list (for now)


class Coin(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y):
        # Call the parent's constructor
        pygame.sprite.Sprite.__init__(self)
        # load image
        path = "Assets/Images/coin"
        self.images = []
        for file_name in os.listdir(path):
            image = pygame.image.load(path + os.sep + file_name).convert_alpha()
            self.images.append(image)
        # set up animation
        self.index = 0
        self.image = self.images[self.index]
        self.animation_frames = 6  # how many frames each image in the animation will last
        self.current_frame = 0
        # place in the center of a tile
        self.tile_x, self.tile_y = tile_x, tile_y
        self.rect = self.image.get_rect()
        self.rect.left = tile_x * TILE_SIZE + TILE_SIZE // 2 - 6
        self.rect.top = tile_y * TILE_SIZE + TILE_SIZE // 2 - 8

    def update(self):
        self.current_frame += 1
        if self.current_frame >= self.animation_frames:  # update animation every few frames
            self.current_frame = 0
            self.index = (self.index + 1) % len(self.images)
            self.image = self.images[self.index]
