import queue
from collections import namedtuple
from Participants import *
from Crossings import *
import csv

Fraction = namedtuple('Fraction', ['numerator', 'denominator'])


def rand_with_probability(prob: Fraction):
    return randint(1, prob[1]) <= prob[0]


class Engine:
    turn_prob_right = Fraction(3, 156)
    turn_prob_left = Fraction(2, 142)

    crossing_open_duration = 40
    crossing_close_duration = 20

    def __init__(self, map: list, pedestrian_areas: list, lights_mode: int):
        self.map_w = len(map)
        self.map_h = len(map[0])
        self.map = map
        self.crossing_closed = False
        self.iter_counter = 0
        self.budryka_cars = [[], []]
        self.kawiory_cars = [[], []]
        self.lights_loop = [20, 60, 20, 40, 20, 50, 20, 60, 80, 10]
        self.loop_max_timestapm = None
        self.loop_timestapm = []
        self.loop_lights_state = None
        self.kijowska_to_spawn = queue.Queue()
        self.ak_to_spawn = queue.Queue()
        self.pedestrian_areas = pedestrian_areas
        self.cars = [[0 for _ in range(3)] for i in range(self.map_w)]
        self.lights_mode = lights_mode
        self.save_stats_every = 20  # number of iterations after which statistics are saved to the file
        self.cars_passed_crossing = 0  # counting cars for statistics
        self.cars_waiting_iters = 0  # counting sum of waiting time for statistics
        self.pedestrians_passed_crossing = 0  # counting pedestrians for statistics
        self.pedestrians_waiting_iters = 0  # counting sum of waiting time for statistics
        self.stats_file_name = "stats.csv"
        two_lanes = [(0, 263), (613, 657), (1168, 1215)]
        crossings = [(230, 255), (622, 645), (1181, 1202)]  # wspolrzedne przejsc z map0
        self.crossing_loop_init()
        self.change_lights_mod(lights_mode)
        self.clear_pedestrians()
        for tup in two_lanes:
            for i in range(tup[0], tup[1]):
                self.cars[i][1] = None

        with open(self.stats_file_name, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Iteration number", "Cars amount", "Sum of waiting time for cars", "Pedestrians amount",
                             "Sum of waiting time for pedestrians"])

    def clear_pedestrians(self):
        for area in self.pedestrian_areas:
            area.clear()

    def is_any_vehicle_there(self, x_from: int, y_from: int, x_to: int, y_to: int) -> bool:
        for x in range(x_from, x_to + 1):
            for y in range(y_from, y_to + 1):
                if is_vehicle(self.cars[x][y]):
                    return True
        return False

    def is_occupied(self, x: int, y: int) -> bool:
        x_ind, y_ind = map_pos_to_arr_ind((x, y))
        if self.cars[x_ind][y_ind] != 0:
            return True
        if y_ind == 0:
            for i in range(1, min(1 + max_veh_len, x_ind + 1)):
                if is_vehicle(self.cars[x_ind - i][y_ind]):
                    car = self.cars[x_ind - i][y_ind]
                    dist = i
                    return dist < car.length
            return False
        else:
            for i in range(1, min(1 + max_veh_len, self.map_w)):
                if is_vehicle(self.cars[x_ind + i][y_ind]):
                    car = self.cars[x_ind + i][y_ind]
                    dist = i
                    return dist < car.length
            return False

    def spawn_cars(self):
        # Budryka & Kawiory
        prob_budryka_spawn = Fraction(14, 1000)
        if rand_with_probability(prob_budryka_spawn):
            car_scooter_prob = Fraction(10, 13)
            initial_pos = (672, 35 + 10 * len(self.budryka_cars[1]))
            if rand_with_probability(car_scooter_prob):
                veh = Car(initial_pos, self.cars)
            else:
                veh = Scooter(initial_pos, self.cars)
            if rand_with_probability(Fraction(1, 2)):
                veh.will_turn = True
            self.budryka_cars[1].append(veh)
        prob_kawiory_spawn = Fraction(1, 300)
        if rand_with_probability(prob_kawiory_spawn):
            car_scooter_prob = Fraction(2, 3)
            initial_pos = (754, 35 + 10 * len(self.kawiory_cars[1]))
            if rand_with_probability(car_scooter_prob):
                veh = Car(initial_pos, self.cars)
            else:
                veh = Scooter(initial_pos, self.cars)
            if rand_with_probability(Fraction(1, 2)):
                veh.will_turn = True
            self.kawiory_cars[1].append(veh)
        # Kijowska
        phase = self.iter_counter % 60
        initial_pos = (self.map_w - 1, 15)
        if 40 > phase >= 0 and not self.is_occupied(initial_pos[0], initial_pos[1]):
            prob_kijowska_spawn = Fraction(1, 15)
            if rand_with_probability(prob_kijowska_spawn):
                self.add_car(Car(initial_pos, self.cars))
        elif phase == 40:
            cars_to_spawn = randint(7, 13)
            for i in range(cars_to_spawn):
                rand = randint(1, 149)
                if rand < 143:
                    self.kijowska_to_spawn.put(Car(initial_pos, self.cars))
                elif rand < 147:
                    self.kijowska_to_spawn.put(BigBus(initial_pos, self.cars))
                elif rand < 149:
                    self.kijowska_to_spawn.put(Bus(initial_pos, self.cars))
                else:
                    self.kijowska_to_spawn.put(Truck(initial_pos, self.cars))
        elif not self.kijowska_to_spawn.empty() and not self.is_occupied(initial_pos[0], initial_pos[1]):
            car = self.kijowska_to_spawn.get()
            if isinstance(car, Car) or isinstance(car, Scooter):
                if rand_with_probability(self.turn_prob_left):
                    car.will_turn = True
            self.add_car(car)
        # Armii Krajowej
        initial_pos = (0, 33)
        phase = self.iter_counter % 120
        if phase == 0:
            cars_to_spawn = randint(13, 19)
            for i in range(cars_to_spawn):
                rand = randint(1, 153)
                if rand < 133:
                    self.ak_to_spawn.put(Car(initial_pos, self.cars))
                elif rand < 141:
                    self.ak_to_spawn.put(BigBus(initial_pos, self.cars))
                elif rand < 147:
                    self.ak_to_spawn.put(Bus(initial_pos, self.cars))
                elif rand < 153:
                    self.ak_to_spawn.put(Scooter(initial_pos, self.cars))
                else:
                    self.ak_to_spawn.put(Truck(initial_pos, self.cars))
        elif phase < 50:
            if not self.is_occupied(initial_pos[0], initial_pos[1]) and not self.ak_to_spawn.empty():
                car = self.ak_to_spawn.get()
                if isinstance(car, Car) or isinstance(car, Scooter):
                    if rand_with_probability(self.turn_prob_right):
                        car.will_turn = True
                self.add_car(car)
        elif not self.is_occupied(initial_pos[0], initial_pos[1]):
            prob_piastowska_spawn = Fraction(2, 35)
            if rand_with_probability(prob_piastowska_spawn):
                self.add_car(Car(initial_pos, self.cars))

    def change_lights_mod(self, i):
        self.lights_mode = i
        match self.lights_mode:
            case 0:
                self.pedestrian_areas[0].clear_road()
                self.pedestrian_areas[0].type = 1
                return
            case 1:
                self.pedestrian_areas[0].clear_road()
                self.pedestrian_areas[0].type = 1
                self.crossing_AK_coordinated()
                return
            case 2:
                self.pedestrian_areas[0].clear_road()
                self.pedestrian_areas[0].type = 1
                return
            case 3:
                self.pedestrian_areas[0].type = 0
                return

    def crossing_loop(self):
        phase = self.iter_counter % self.loop_max_timestapm
        for stamp in self.loop_timestapm:
            if stamp[0] == phase:
                self.loop_lights_state = stamp[1]
        if self.loop_lights_state == 1:
            self.crossing_closed = False
            self.paint_lights_crossing(6, 3)
        else:
            self.crossing_closed = True
            self.paint_lights_crossing(3, 6)

    def crossing_loop_init(self):
        stamp = 0
        self.loop_timestapm.append((stamp, 0))
        for elem in self.lights_loop:
            stamp += elem
            self.loop_timestapm.append((stamp, 1))
            stamp += 15
            self.loop_timestapm.append((stamp, 0))
        self.loop_max_timestapm = self.loop_timestapm[-1][0]

    def traffic_lights_crossing(self):
        match self.lights_mode:
            case 0:
                self.crossing_loop()
                return
            case 1:
                self.crossing_AK_coordinated()
                return
            case 2:
                pass
            case 3:
                self.crossing_closed = False
                self.paint_lights_crossing(6, 3)
                return

        if self.crossing_closed is False and \
                self.iter_counter % (Engine.crossing_close_duration + Engine.crossing_open_duration) == 0:
            self.crossing_closed = True
            self.paint_lights_crossing(3, 6)

        if self.crossing_closed is True and self.iter_counter % (
                Engine.crossing_close_duration + Engine.crossing_open_duration) == Engine.crossing_open_duration:
            self.crossing_closed = False
            self.paint_lights_crossing(6, 3)

    def paint_lights_crossing(self, color_from: int, color_to: int):
        # 3 - green, 6 - red
        if (color_from != 3 and color_from != 6) or (color_to != 3 and color_to != 6):
            raise Exception("Cannot paint crossing into other color than red or green")
        for i in range(229, 255):
            for j in range(14, 34):
                if self.map[i][j] == color_from:  # crossing
                    self.map[i][j] = color_to  # crossing_close

    def crossing_AK_coordinated(self):
        phase = self.iter_counter % 120
        if phase < 100 and not self.crossing_closed:
            self.crossing_closed = True
            self.paint_lights_crossing(3, 6)
        elif phase == 100:
            self.crossing_closed = False
            self.paint_lights_crossing(6, 3)

    def iteration(self):
        self.spawn_cars()
        self.traffic_lights_crossing()
        self.spawn_pedestrians()
        self.move_pedestrians()
        self.move_cars()
        self.update_stats_file()
        self.iter_counter += 1

    def move_cars(self):
        cars_copy = copy.deepcopy(self.cars)
        for x in range(self.map_w):
            for y in range(len(cars_copy[x])):
                if is_vehicle(cars_copy[x][y]):
                    self.cars[x][y].set_speed()
                    if y == 0 and 254 <= x <= 500 and self.cars[x][y].speed < 5 and not self.crossing_closed:
                        self.cars_waiting_iters += 1
                    elif y != 0 and 20 <= x <= 230 and self.cars[x][y].speed < 5 and not self.crossing_closed:
                        self.cars_waiting_iters += 1
        for x in range(self.map_w):
            if is_vehicle(cars_copy[x][0]):
                new_x = x - self.cars[x][0].speed
                if new_x >= 0:
                    if self.cars[x][0].will_turn and new_x == 742:
                        if not self.is_any_vehicle_there(742 - 2 * max_veh_speed, 1, 742 + 6, 2):
                            self.move_car(x, 0, new_x, 3)
                    elif self.cars[x][0].will_turn and new_x <= 660:
                        if not self.is_any_vehicle_there(660 - 2 * max_veh_speed, 1, 660 + 6, 2):
                            self.move_car(x, 0, 660, 3)
                        else:
                            self.move_car(x, 0, 660, 0)
                    else:
                        self.move_car(x, 0, new_x, 0)
                else:
                    self.cars[x][0] = 0
            if is_vehicle(cars_copy[x][1]):
                new_x = x + self.cars[x][1].speed
                if new_x < self.map_w:
                    if self.cars[new_x][1] is not None:
                        self.move_car(x, 1, new_x, 1)
                    else:
                        self.move_car(x, 1, new_x, 2)
                else:
                    self.cars[x][1] = 0
            if is_vehicle(cars_copy[x][2]):
                new_x = x + self.cars[x][2].speed
                if new_x < self.map_w:
                    if self.cars[x][2].will_turn and new_x >= 645:
                        if new_x >= 742:
                            self.move_car(x, 2, new_x, 3)
                        elif new_x == 660:
                            self.move_car(x, 2, new_x, 3)
                        else:
                            self.move_car(x, 2, new_x, 2)
                    elif self.cars[x][2].preferred_lane == 'l' and self.cars[x][1] is not None:
                        self.move_car(x, 2, new_x, 1)
                    else:
                        self.move_car(x, 2, new_x, 2)
                else:
                    self.cars[x][2] = 0
        self.move_cars_from_list(self.budryka_cars[1], True)
        self.move_cars_from_list(self.kawiory_cars[1], True)
        self.move_cars_from_list(self.budryka_cars[0], False)
        self.move_cars_from_list(self.kawiory_cars[0], False)

    def move_cars_from_list(self, cars_list: list, upwards: bool):
        if len(cars_list) == 0:
            return
        if not upwards:
            i = len(cars_list) - 1
            while i >= 0:
                car = cars_list[i]
                car.position = (car.position[0], car.position[1] + 10)
                if car.position[1] > 70:
                    cars_list.pop(i)
                i -= 1
            return
        car = cars_list[0]
        if car.position[1] > 34:
            car.position = (car.position[0], 34)
            return
        can_turn_right = True
        if self.is_occupied(car.position[0] + 1, 27) or self.is_occupied(car.position[0] + 1, 33):
            return
        for i in range(0, 3 * max_veh_speed):
            if is_vehicle(self.cars[car.position[0] - i][2]) or is_vehicle(self.cars[car.position[0] - i][1]):
                can_turn_right = False
                break
        if not can_turn_right:
            return
        if not car.will_turn:
            self.move_car(car.position[0], 3, car.position[0] + 1, 1)
            car.speed = car.acceleration
            for car in cars_list:
                car.position = (car.position[0], car.position[1] - 10)
            return
        can_turn_left = True
        if self.is_occupied(car.position[0] - 1, 15):
            return
        for i in range(0, 3 * max_veh_speed):
            if is_vehicle(self.cars[car.position[0] + i][0]):
                can_turn_left = False
                break
        if can_turn_left:
            car.will_turn = False
            self.move_car(car.position[0], 3, car.position[0] - 1, 0)
            car.speed = car.acceleration
            for car in cars_list:
                car.position = (car.position[0], car.position[1] - 10)

    def move_car(self, x_from, y_from, x_to, y_to):
        if x_to == x_from and y_from == y_to:
            return
        if y_to != 3 and is_vehicle(self.cars[x_to][y_to]):
            raise Exception("2 cars cannot be on one field")
        if y_from == 3:
            if x_from < 700:
                self.cars[x_to][y_to] = self.budryka_cars[1].pop(0)
            else:
                self.cars[x_to][y_to] = self.kawiory_cars[1].pop(0)
            y_pos = 27
            if y_to == 0:
                y_pos = 15
            self.cars[x_to][y_to].position = (x_to, y_pos)
            return
        if y_to == 3:
            if x_to == 660:
                self.budryka_cars[0].append(self.cars[x_from][y_from])
            else:
                self.kawiory_cars[0].append(self.cars[x_from][y_from])
                x_to = 742
            self.cars[x_from][y_from].position = (x_to, 34)
            self.cars[x_from][y_from] = 0
            return
        if x_to <= 230 < x_from or x_from <= 230 < x_to:
            self.cars_passed_crossing += 1
        if y_to == y_from:
            self.cars[x_from][y_from].position = (x_to, self.cars[x_from][y_to].position[1])
        elif y_to == 2:
            self.cars[x_from][y_from].position = (x_to, 33)
        elif y_to == 1:
            self.cars[x_from][y_from].position = (x_to, 27)
        elif y_to == 0:
            self.cars[x_from][y_from].position = (x_to, 15)
        else:
            print("Unknown position")
        self.cars[x_to][y_to] = self.cars[x_from][y_from]
        self.cars[x_from][y_from] = 0

    def spawn_pedestrians(self):

        for area in self.pedestrian_areas:
            if area.type == 1 and not self.crossing_closed:
                continue
            if area.type == 0 and area.car_closed:
                continue
            if area.type == 0 and area.pedestrian_end:
                if area.end_delay < 0:
                    area.end_delay -= 1
                    continue
                area.pedestrian_end = False
                area.end_delay = area.max_end_delay

            if randint(0, 100) <= area.spawn_prob:
                if area.type == 0:
                    area.car_closed = True
                if randint(1, 2) == 1:
                    area.spawn_pedestrian_up()
                else:
                    area.spawn_pedestrian_down()
                if area.width_range[0] == 230:
                    self.pedestrians_passed_crossing += 1

    def move_pedestrians(self):

        for area in self.pedestrian_areas:
            if area.type == 1 and self.crossing_closed:
                self.pedestrians_waiting_iters += area.get_pedestrians_number()
                continue
            area.iterate()

    def add_car(self, vehicle):
        pos = map_pos_to_arr_ind(vehicle.position)
        self.cars[pos[0]][pos[1]] = vehicle

    def can_pass_crossing(self, crossing_num: int) -> bool:
        # 0 - crossing with lights, 1 - crossing near Budryka, 2 - crossing near D17
        if crossing_num < 0 or crossing_num > 2:
            raise Exception("Wrong crossing number")
        if self.pedestrian_areas[crossing_num].type == 1 and self.crossing_closed:
            return True
        if self.pedestrian_areas[crossing_num].type == 0 and not self.pedestrian_areas[crossing_num].car_closed:
            return True
        return False

    def update_stats_file(self):
        if self.iter_counter % self.save_stats_every == 0:
            with open(self.stats_file_name, "a") as file:
                file.write(f"{self.iter_counter},{self.cars_passed_crossing},{self.cars_waiting_iters},"
                           f"{self.pedestrians_passed_crossing},{self.pedestrians_waiting_iters}\n")
