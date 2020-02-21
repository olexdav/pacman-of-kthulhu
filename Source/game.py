import os
import numpy as np
import random
import pygame

TILE_SIZE = 60
PACMAN_MOVE_FRAMES = 20
PACMAN_AI_DEPTH = 10


# parameters that dictate how hard the game becomes at each difficulty level
difficulty_settings = {
    0: {"ghost_frames_per_tile": 99, "ghost_amount": 0},
    1: {"ghost_frames_per_tile": 40, "ghost_amount": 1},
    2: {"ghost_frames_per_tile": 30, "ghost_amount": 1},
    3: {"ghost_frames_per_tile": 20, "ghost_amount": 1},
    4: {"ghost_frames_per_tile": 40, "ghost_amount": 2},
    5: {"ghost_frames_per_tile": 30, "ghost_amount": 2},
    6: {"ghost_frames_per_tile": 40, "ghost_amount": 3},
}


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
    def __init__(self, width, height, difficulty=0, ghosts_n_coins=True):
        self.width = width
        self.height = height
        self.player_spawn_point = (height // 2, width // 2)
        self.difficulty = difficulty
        self.tile_map = None
        self.generate_tile_map()
        self.ghosts = pygame.sprite.RenderPlain()
        self.coins = pygame.sprite.RenderPlain()
        if ghosts_n_coins:
            self.add_ghosts()
            self.place_coins()
        self.score = 0

    def update(self):
        self.coins.update()

    # generates a tile map in-place
    def generate_tile_map(self):
        width, height = self.width, self.height
        tile_map = np.zeros((height, width), dtype=int)
        # surround map with impassable wall border
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
    def add_random_walls(self, chance=0.15):
        # create list of points
        points = []
        for x in range(2, self.width - 1, 2):
            for y in range(1, self.height - 1, 2):
                points.append((y, x))
        for x in range(1, self.width - 1, 2):
            for y in range(2, self.height - 1, 2):
                points.append((y, x))
        random.shuffle(points)
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

    def add_ghosts(self):
        params = difficulty_settings[self.difficulty]
        ghost_frames_per_tile = params["ghost_frames_per_tile"]
        ghost_amount = params["ghost_amount"]
        # pick random locations away from the center of the maze
        spawn_points = self.get_random_locations_in_corners(ghost_amount)
        for spawn_y, spawn_x in spawn_points:
            ghost = Ghost(spawn_x, spawn_y, ghost_frames_per_tile)
            self.ghosts.add(ghost)

    # get up to 4 random locations in different corners of the map
    def get_random_locations_in_corners(self, points_amount=4):
        quadrant_w, quadrant_h = self.width // 3, self.height // 3
        x_right = (self.width * 2) // 3 - 1
        y_bottom = (self.height * 2) // 3 - 1
        quadrant_topleft_points = [(1, 1), (1, x_right), (y_bottom, 1), (y_bottom, x_right)]
        points = []
        for qy, qx in quadrant_topleft_points:
            point = 0, 0
            while self.tile_map[point[0], point[1]] != 0:  # find a random empty tile in quadrant
                point = qy + random.randint(0, quadrant_h-1), qx + random.randint(0, quadrant_w-1)
            points.append(point)
        random.shuffle(points)
        return points[:points_amount]

    # places coins all over the map, except for the spawn point
    def place_coins(self):
        center_x, center_y = self.width // 2, self.height // 2
        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                if abs(center_x - x) > 1 or abs(center_y - y) > 1: # exclude spawn point
                    self.add_coin(x, y)
                    #if self.tile_map[y, x] == 0:
                    #    self.coins.add(Coin(x, y))

    def add_coin(self, tile_x, tile_y):
        if self.tile_map[tile_y, tile_x] == 0:  # place coins in empty corridors
            # check that the new coin does not intersect with other coins
            intersect = False
            for coin in self.coins:
                if coin.tile_y == tile_y and coin.tile_x == tile_x:
                    intersect = True
                    break
            if not intersect:
                self.coins.add(Coin(tile_x, tile_y))


class Character(pygame.sprite.Sprite):
    def __init__(self, tile_x, tile_y):
        # Call the parent's constructor
        pygame.sprite.Sprite.__init__(self)
        # movement
        self.curr_tile_x, self.curr_tile_y = tile_x, tile_y
        self.move_frame = 0
        self.curr_move = None  # current direction of movement
        self.planned_moves = []
        self.sprite_offset_x = 0  # move a sprite a bit to the right to center it
        self.move_frames = None
        self.rect = None

    # updates movement for 1 frame, following and executing planned_moves
    def move(self):
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
            self.rect.left = self.rect.left + self.sprite_offset_x
            self.rect.top = int((self.curr_tile_y + self.curr_move[0] * movement_percent) * TILE_SIZE)
            if self.move_frame >= self.move_frames:  # finish move
                self.curr_tile_x += self.curr_move[1]
                self.curr_tile_y += self.curr_move[0]
                self.curr_move = None


class PacMan(Character):
    def __init__(self, tile_x, tile_y):
        # Call the parent's constructor
        super(PacMan, self).__init__(tile_x, tile_y)
        # load image
        self.pacman_image = pygame.image.load("Assets/Images/pacman.png").convert_alpha()
        self.scared_image = pygame.image.load("Assets/Images/pacman_scared.png").convert_alpha()
        self.current_image = self.pacman_image
        self.dead_image = pygame.image.load("Assets/Images/pacman_dead.png").convert_alpha()
        self.image = self.pacman_image
        self.rect = self.image.get_rect()
        self.rect.left = tile_x * TILE_SIZE
        self.rect.top = tile_y * TILE_SIZE
        # movement
        self.move_frames = PACMAN_MOVE_FRAMES  # how many frames it takes to move one cell
        # being eaten by ghosts
        self.dead = False

    def update(self, level):
        if self.dead:  # dead men tell no tales
            return
        self.move()
        if self.curr_move:  # rotate sprite towards movement
            self.rotate_towards_direction(self.curr_move)
        # movement finished: search for new targets
        if not self.curr_move and not self.planned_moves and level.coins:
            for coin in level.coins:
                # if pacman is on top of the coin, consume it immediately
                if self.curr_tile_x == coin.tile_x and self.curr_tile_y == coin.tile_y:
                    coin.kill()  # devour the coin
                    level.score += 10  # claim some points
            if level.coins:
                self.planned_moves = [self.choose_best_move(level)]
            #    else:  # try to reach the coin
            #        #self.planned_moves = level.find_shortest_path(self.curr_tile_x, self.curr_tile_y,
            #        #                                              coin.tile_x, coin.tile_y)
            #        break  # only try to eat the first coin on the list (for now)

    def rotate_towards_direction(self, direction):
        angles = {(0, 1): 0, (0, -1): 180, (-1, 0): 90, (1, 0): 270}
        self.image = pygame.transform.rotate(self.current_image, angles[direction])

    def die(self):
        self.dead = True
        self.image = self.dead_image

    def choose_best_move(self, level):
        # fetch current game state
        curr_state = self.fetch_game_state(level)
        # find a strategy that lets pacman eat the most coins
        return curr_state.pick_best_move(level, self)

    def fetch_game_state(self, level):
        # save pacman location
        game_state = GameState(None, self.curr_tile_x, self.curr_tile_y)
        # save ghost locations
        game_state.ghosts = []
        for g in level.ghosts:
            ghost = GhostPosition()
            ghost.get_from_ghost(g)
            game_state.ghosts.append(ghost)
        return game_state


class GhostPosition:
    def __init__(self):
        self.tile_x = 0
        self.tile_y = 0
        self.move_dir = None
        self.move_progress = 0
        self.move_frames = 0  # how many frames it takes to move one cell

    def get_from_ghost(self, ghost):
        self.tile_x = ghost.curr_tile_x
        self.tile_y = ghost.curr_tile_y
        self.move_dir = ghost.curr_move
        self.move_progress = ghost.move_frame
        self.move_frames = ghost.move_frames

    def copy_from_other(self, other):
        self.tile_x = other.tile_x
        self.tile_y = other.tile_y
        self.move_dir = other.move_dir
        self.move_progress = other.move_progress
        self.move_frames = other.move_frames


class GameState:
    def __init__(self, parent, pacman_x, pacman_y, depth=0, ghosts=None, picked_coins=[], move_here=None):
        self.parent = parent
        self.children = []
        self.pacman_x, self.pacman_y = pacman_x, pacman_y
        self.ghosts = ghosts  # list of ghost positions
        self.depth = depth
        self.picked_coins = picked_coins  # coordinates of coins picked up by pacman on the way
        self.picked_coin_now = False  # whether pacman just picked a coin by his (last) move here
        self.move_here = move_here  # a last move that lead pacman into this state

    @staticmethod
    def is_direction_opposite(dir1, dir2):
        return dir1[0] == -dir2[0] and dir1[1] == -dir2[1]

    def evaluate_children(self, level):
        if self.depth >= PACMAN_AI_DEPTH:  # stop evaluating children after a certain depth
            return
        # simulate ghost movement
        new_ghosts = self.simulate_ghosts_movement(level)
        # find valid moves
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        for direction in directions:
            # don't allow backtracking
            if self.move_here:
                if not self.picked_coin_now and GameState.is_direction_opposite(direction, self.move_here):
                # if GameState.is_direction_opposite(direction, self.move_here):
                    continue
            target_y = self.pacman_y + direction[0]
            target_x = self.pacman_x + direction[1]
            if level.tile_map[target_y, target_x] == 0:  # move only through corridors
                new_state = GameState(self, target_x, target_y, self.depth+1,
                                      new_ghosts, self.picked_coins.copy(), direction)
                if not new_state.is_deadly():
                    new_state.pick_coin(level)
                    new_state.evaluate_children(level)  # evaluate a new state recursively
                    self.children.append(new_state)

    def pick_random_move(self, level):
        directions = [(0, 1), (0, -1), (-1, 0), (1, 0)]
        possible_moves = []
        for direction in directions:
            target_y = self.pacman_y + direction[0]
            target_x = self.pacman_x + direction[1]
            if level.tile_map[target_y, target_x] == 0:  # move only through corridors
                possible_moves.append(direction)
        return random.choice(possible_moves)

    def pick_best_move(self, level, pacman):
        self.evaluate_children(level)
        #richest_leaf = self.get_richest_leaf()
        #return self.get_first_move_towards(richest_leaf)
        # search for the closest coin
        closest_coin_state = self.get_closest_coin_state()
        if closest_coin_state:
            pacman.current_image = pacman.pacman_image
            return self.get_first_move_towards(closest_coin_state)
        else:  # the situation is hopeless at this point, just panic
            pacman.current_image = pacman.scared_image  # be frightened
            return self.pick_random_move(level)

    # find game state that yields a coin in a smallest amount of moves
    # if no such state exists, move randomly
    def get_closest_coin_state(self):
        queue = [self]
        leaves = []
        while queue:  # breadth-first search
            curr_state = queue.pop(0)
            if curr_state.picked_coins:
                # TODO: check if this state ensures survival after picking up the coin
                # check if the state has at least one descendant at max depth that is not deadly
                if curr_state.has_surviving_leaves():
                    return curr_state  # closest state found!
            if curr_state.children:
                for child in curr_state.children:
                    queue.append(child)
            elif curr_state.depth == PACMAN_AI_DEPTH:
                leaves.append(curr_state)
        # if no path within the field of vision yields a coin, move randomly
        if leaves:
            return random.choice(leaves)

    # check whether a state has at least one descendant at max depth that is not deadly
    def has_surviving_leaves(self):
        stack = [self]  # depth-first search
        while stack:
            curr_state = stack.pop()
            if curr_state.depth == PACMAN_AI_DEPTH-1:
                return True
            if curr_state.children:
                for child in curr_state.children:
                    stack.append(child)
        return False  # no survival strategy found

    # find leaf strategy that gives the most money
    def get_richest_leaf(self):
        if not self.children:
            return self
        richest_leaves = [child.get_richest_leaf() for child in self.children]
        # TODO: choose closest max value
        coins_amount = [len(leaf.picked_coins) for leaf in richest_leaves]
        richest_leaf = richest_leaves[np.argmax(np.array(coins_amount))]
        return richest_leaf

    # find first move that pacman has to take to reach from "self" to "state"
    def get_first_move_towards(self, state):
        curr_node = state
        while curr_node.parent != self:
            curr_node = curr_node.parent
        return curr_node.move_here

    # check if pacman gets eaten in this state
    def is_deadly(self):
        for ghost in self.ghosts:  # check for pacman and ghost collisions
            if self.check_collision(ghost):
                return True
        return False

    # check if a ghost is in range of pacman
    def check_collision(self, ghost, clear_range=1.2):
        ghost_y = ghost.tile_y + ghost.move_dir[0] * ghost.move_progress / ghost.move_frames
        ghost_x = ghost.tile_x + ghost.move_dir[1] * ghost.move_progress / ghost.move_frames
        px, py = self.pacman_x, self.pacman_y
        # try to maintain at least clear_range tiles from a ghost
        return ((ghost_y-py)**2 + (ghost_x-px)**2)**0.5 < clear_range

    # pick a coin if it is located in the same tile as pacman
    def pick_coin(self, level):
        pac_pos = self.pacman_y, self.pacman_x
        if pac_pos in self.picked_coins:  # check if the coin is already picked
            return
        for coin in level.coins:  # check if pacman is currently standing on a coin
            if coin.tile_x == self.pacman_x and coin.tile_y == self.pacman_y:
                self.picked_coins.append((coin.tile_y, coin.tile_x))  # pick up a coin
                self.picked_coin_now = True

    # simulate movement for a list of ghost positions and return a new list
    def simulate_ghosts_movement(self, level):
        return [self.simulate_ghost_movement(g, level) for g in self.ghosts]

    def simulate_ghost_movement(self, old_ghost, level):
        ghost = GhostPosition()  # create a copy of the ghost
        ghost.copy_from_other(old_ghost)
        if not ghost.move_dir:  # pick a good move
            ghost.move_dir = self.pick_good_ghost_move(ghost, level)
        ghost.move_progress += PACMAN_MOVE_FRAMES
        while ghost.move_progress >= ghost.move_frames:  # move as time passes
            ghost.tile_y += ghost.move_dir[0]
            ghost.tile_x += ghost.move_dir[1]
            # pick a good move
            ghost.move_dir = self.pick_good_ghost_move(ghost, level)
            ghost.move_progress -= ghost.move_frames
        return ghost

    def pick_good_ghost_move(self, ghost, level):
        path_moves = level.find_shortest_path(ghost.tile_x, ghost.tile_y,
                                              self.pacman_x, self.pacman_y)
        return path_moves[0]


class Ghost(Character):
    def __init__(self, tile_x, tile_y, move_frames):
        # Call the parent's constructor
        super(Ghost, self).__init__(tile_x, tile_y)
        # load image
        self.spooky_image = pygame.image.load("Assets/Images/spooky.png").convert_alpha()
        self.image = self.spooky_image
        self.rect = self.image.get_rect()
        self.rect.left = tile_x * TILE_SIZE
        self.rect.top = tile_y * TILE_SIZE
        self.sprite_offset_x = 5
        # movement
        self.move_frames = move_frames  # how many frames it takes to move one cell

    def update(self, level, pacman):
        self.move()
        if self.curr_move:  # flip sprite towards movement
            self.flip_towards_direction(self.curr_move)
        # check for collision with pacman
        px, py = pacman.rect.centerx, pacman.rect.centery
        gx, gy = self.rect.centerx, self.rect.centery
        pacman_dist = ((px-gx)**2 + (py-gy)**2) ** 0.5
        if pacman_dist < TILE_SIZE * 0.9:  # pacman in range
            pacman.die()  # murder pacman
        # movement finished: search for a path towards pacman
        if not self.curr_move and not self.planned_moves:
            pacman_x, pacman_y = pacman.curr_tile_x, pacman.curr_tile_y
            moves_to_pacman = level.find_shortest_path(self.curr_tile_x, self.curr_tile_y,
                                                       pacman_x, pacman_y)
            self.planned_moves = moves_to_pacman[:1]  # take only the first move

    # make the ghost face the direction of movement
    def flip_towards_direction(self, direction):
        if direction == (0, 1) or direction == (0, -1):  # update image when moving sideways
            self.image = pygame.transform.flip(self.spooky_image, direction == (0, 1), 0)


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
        self.index = random.randint(0, len(self.images)-1)  # random animation index
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
