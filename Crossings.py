from random import randint
import copy
from Participants import Pedestrian


class PedestrianCrossing:
    def __init__(self, width_range, up_spawn_range, down_spawn_range, type, spawn_prob):
        self.spawn_prob = spawn_prob
        self.type = type  # 0 for crossing without lights, 1 for crossing with lights
        self.width_range = width_range
        self.up_spawn_range = up_spawn_range
        self.down_spawn_range = down_spawn_range
        self.total_width = width_range[1] - width_range[0] + 1
        self.total_height = down_spawn_range[1] - up_spawn_range[0] + 1
        self.max_spawn_delay = 1
        self.max_end_delay = 10
        self.spawn_delay = self.max_spawn_delay
        self.end_delay = self.max_end_delay
        self.car_closed = False
        self.pedestrian_end = False
        self.map = []
        for i in range(self.total_width):
            self.map.append([])
            for j in range(self.total_height):
                self.map[i].append([])

    def spawn_pedestrian_up(self):
        x = randint(0, self.total_width - 1)
        y = randint(self.up_spawn_range[0], self.up_spawn_range[1]) - self.up_spawn_range[0]
        self.map[x][y].append(Pedestrian((x, y), -1))

    def spawn_pedestrian_down(self):
        x = randint(0, self.total_width - 1)
        y = randint(self.down_spawn_range[0], self.down_spawn_range[1]) - self.up_spawn_range[0]
        self.map[x][y].append(Pedestrian((x, y), 1))

    def move(self):
        map_copy = copy.deepcopy(self.map)
        self.map = [[[] for _ in range(self.total_height)] for _ in range(self.total_width)]
        for i in range(self.total_width):
            for j in range(self.total_height):
                if len(map_copy[i][j]) != 0:
                    for elem in map_copy[i][j]:
                        if (elem.direction == -1 and j >= self.down_spawn_range[0] - self.up_spawn_range[0] - 1) \
                                or (elem.direction == 1 and j <= self.up_spawn_range[1] - self.up_spawn_range[0]):
                            continue
                        self.map[i][j - (elem.direction * elem.speed)].append(elem)

    def update_speed(self):
        for i in range(self.total_width):
            for j in range(self.total_height):
                if len(self.map[i][j]) != 0:
                    for elem in self.map[i][j]:
                        elem.speed = min(Pedestrian.max_speed, elem.speed + 1)

    def is_anyone_at_crossing(self):
        for i in range(self.total_width):
            for j in range(self.total_height):
                if len(self.map[i][j]) != 0:
                    return True
        return False

    def iterate(self):
        if self.car_closed and self.spawn_delay > 0:
            self.spawn_delay -= 1
            return

        self.update_speed()
        self.move()

        if not self.is_anyone_at_crossing() and self.car_closed:
            self.pedestrian_end = True
            self.car_closed = False
            self.spawn_delay = self.max_spawn_delay

    def get_pedestrians_number(self):
        counter = 0
        for x in range(self.total_width):
            for y in range(self.total_height):
                counter += len(self.map[x][y])
        return counter

    def clear(self):
        for x in range(self.total_width):
            for y in range(self.total_height):
                self.map[x][y] = []

    def clear_road(self):
        for x in range(self.total_width):
            for y in range(self.up_spawn_range[1] - self.up_spawn_range[0],
                           self.down_spawn_range[0] - self.up_spawn_range[0]):
                self.map[x][y] = []
