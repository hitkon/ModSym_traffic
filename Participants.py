import random
from abc import abstractmethod


def is_vehicle(obj) -> bool:
    if obj is None or obj == 0:
        return False
    return True


def map_pos_to_arr_ind(position: tuple):
    if position[1] < 21:
        return position[0], 0
    if position[1] < 28:
        return position[0], 1
    if position[1] < 34:
        return position[0], 2
    return position[0], 3


bus_stop_cord = 330
max_veh_len = 36
max_veh_speed = 28


class RoadVehicle:
    look_ahead_variable = 30
    engine = None

    @abstractmethod
    def __init__(self, position: (int, int), map: list):
        # all in cell units
        self.position = position
        self.speed = 0
        self.map = map
        self.preferred_lane = 'l'  # 'l' for left, 'r' for right
        self.will_switch = False
        self.iters_to_wait = 25  # how much time does a bus need to wait on a bus stop
        self.will_turn = False
        self.chosen_route = 0  # for choosing Budryka/Kawiory (0/1) turn
        self.acceleration = 0
        self.width = 0
        self.length = 0
        self.max_speed = 28  # 50km/h = 14m/s
        self.can_turn = False  # True if the vehicle can turn on the crossings
        self.stops = False  # True if the vehicle stops at the bus stop

    def distance_to_static_obstacle(self) -> int:
        x, y = map_pos_to_arr_ind(self.position)
        found_so_far = 1390
        # determine direction
        if y == 0:
            if x > 1202 and not RoadVehicle.engine.can_pass_crossing(2):
                return x - 1202
            elif x > 644 and not RoadVehicle.engine.can_pass_crossing(1):
                found_so_far = x - 644
            elif x > 254 and not RoadVehicle.engine.can_pass_crossing(0):
                found_so_far = x - 254
        else:
            if x < 230 and not RoadVehicle.engine.can_pass_crossing(0):
                return 230 - x
            elif x < 626 and not RoadVehicle.engine.can_pass_crossing(1):
                found_so_far = 626 - x
            elif x < 1181 and not RoadVehicle.engine.can_pass_crossing(2):
                found_so_far = 1181 - x
        # special events
        if self.will_turn:
            if self.chosen_route == 0:
                return min(abs(660 - x) + 1, found_so_far)
            else:
                return min(abs(742 - x) + 1, found_so_far)
        if self.stops and y == 2:
            if x < bus_stop_cord:
                return bus_stop_cord - x + 1
            if x == bus_stop_cord and self.iters_to_wait > 0:
                self.iters_to_wait -= 1
                return 0

        return found_so_far

    def distance_to_moving_obstacle(self) -> int:
        x, y = map_pos_to_arr_ind(self.position)
        if y == 0:
            for i in range(1, self.speed + self.acceleration + 1 + max_veh_len):
                if x - i < 0:
                    return self.speed + self.acceleration + 1 + max_veh_len
                if is_vehicle(self.map[x - i][y]):
                    return i - self.map[x - i][y].length
        else:
            found_so_far = self.speed + self.acceleration + 1 + max_veh_len
            for i in range(1, self.speed + self.acceleration + 1 + max_veh_len):
                if x + i >= len(self.map):
                    break
                if is_vehicle(self.map[x + i][y]):
                    found_so_far = i - self.map[x + i][y].length
                    break
            if self.will_switch:
                if y == 1:
                    y += 1
                else:
                    y -= 1
                for i in range(0, -max_veh_speed, -1):
                    if x + i >= 0 and self.map[x + i][y] is None:
                        break
                    if x + i >= 0 and is_vehicle(self.map[x + i][y]):
                        return 0
                for i in range(1, self.speed + self.acceleration + 1 + max_veh_len):
                    if x + i >= len(self.map):
                        return min(self.speed + self.acceleration + 1 + max_veh_len, found_so_far)
                    if x + i >= 0 and is_vehicle(self.map[x + i][y]):
                        return min(i - self.map[x + i][y].length, found_so_far)
                return found_so_far
            else:
                return found_so_far
        return self.speed + self.acceleration + 1 + max_veh_len

    def update_will_switch(self):
        self.will_switch = False
        if self.preferred_lane == 'r':
            return
        x, y = map_pos_to_arr_ind(self.position)
        if y == 0:
            return
        if y == 1:
            for i in range(1, self.speed + self.acceleration + 1):
                if x + i >= len(self.map):
                    return
                if self.map[x + i][y] is None:
                    self.will_switch = True
                    return
            return
        if y == 2:
            for i in range(1, self.speed + self.acceleration + 1):
                if x + i > len(self.map):
                    return
                if self.map[x + i][y - 1] is not None:
                    self.will_switch = True
                    return

    def accelerate(self, distance_to_obstacle):
        if self.speed < self.max_speed and self.speed < distance_to_obstacle:
            self.speed = min(self.speed + self.acceleration, self.max_speed, distance_to_obstacle - 1)

    def brake(self, distance_to_obstacle):
        if self.speed >= distance_to_obstacle:
            self.speed = max(min(self.speed - self.acceleration, distance_to_obstacle - 1), 0)

    def avoid_crossing_stay(self):
        x, y = map_pos_to_arr_ind(self.position)
        if 230 <= x + self.speed <= 254 and y > 0:
            for i in range(max_veh_len + self.length):
                if is_vehicle(self.map[254 + i][2]) and self.map[254 + i][2].speed < 6:
                    self.speed = max(230 - self.position[0], 0)

    def set_speed(self):
        self.update_will_switch()
        dist = min(self.distance_to_moving_obstacle(), self.distance_to_static_obstacle() // 2 + 1)
        self.accelerate(dist)
        self.brake(dist)
        self.avoid_crossing_stay()


class Car(RoadVehicle):
    def __init__(self, position, map, will_turn=False):
        super().__init__(position, map)
        self.acceleration = 4
        self.width = 4
        self.length = 9
        self.can_turn = True
        self.will_turn = will_turn
        self.max_speed = 28
        self.chosen_route = random.randint(0, 1) == 1


class Bus(RoadVehicle):
    def __init__(self, position, map):
        super().__init__(position, map)
        self.acceleration = 3
        self.width = 5
        self.length = 24
        if random.randint(0, 1) == 0:
            self.stops = True
        self.preferred_lane = 'r'
        self.max_speed = 24


class BigBus(RoadVehicle):
    def __init__(self, position, map):
        super().__init__(position, map)
        self.acceleration = 3
        self.width = 5
        self.length = 36
        self.stops = True
        self.preferred_lane = 'r'
        self.max_speed = 24


class Truck(RoadVehicle):
    def __init__(self, position, map):
        super().__init__(position, map)
        self.acceleration = 2
        self.width = 6
        self.length = 22
        self.max_speed = 22


class Scooter(RoadVehicle):
    def __init__(self, position, map, will_turn=False):
        super().__init__(position, map)
        self.acceleration = 3
        self.width = 2
        self.length = 4
        self.can_turn = True
        self.will_turn = will_turn
        self.chosen_route = random.randint(0, 1) == 1


class Pedestrian:
    width = 1
    length = 1
    speed = 0
    max_speed = 2

    def __init__(self, position, direction):
        self.position = position
        self.direction = direction
