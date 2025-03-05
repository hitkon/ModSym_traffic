import pygame
import sys
import Engine


class Board:
    def __init__(self, initial_lights_mode=0, initial_simulation_speed=0, end_after=None, display_needed=True):
        self.pedestrian_areas = []
        self.total_width = None
        pygame.init()
        self.clock = pygame.time.Clock()
        self.main_window_size = self.main_window_width, self.main_window_height = 1200, 420
        self.sub_window_size = self.sub_window_width, self.sub_window_height = 1200, 210
        self.speed = [1, 1]
        self.cell_size = 3
        self.scroll_x = 0
        self.scroll_vel = 4
        self.main_screen = None
        self.sub_screen = None
        self.legend_elems = []
        self.legend_labels = ["Legend:", "Pavement", "Road", "Crossing", "Vehicle", "Pedestrian", "Crossing closed"]
        self.speed_cont_vals = [1, 2, 3, 4, 5, 10, 25, 50, 100]
        self.chosen_speed = initial_simulation_speed  # index of array above
        self.light_modes_labels = ["Original", "Crossing synch", "Time loop", "No lights"]
        self.chosen_mode = initial_lights_mode  # index of array above
        self.modes_buttons_cords = []
        self.speed_cont_x = 600
        self.button_width = 15
        self.map = []
        self.map_h, self.map_w = 0, 0
        # colors_ids: 0 - not usable, 1 - pavement, 2 - road, 3 - crossing, 4 - vehicle, 5 - pedestrian, 6 - crossing_closed
        self.colors = [(255, 255, 255), (155, 155, 155), (0, 0, 102), (0, 102, 51), (255, 255, 102), (0, 0, 0),
                       (255, 0, 0)]
        self.cell_size = 3
        self.scroll_vel = 4
        self.font = pygame.font.Font(None, 30)
        self.scrollbar_x = 0
        self.scrollbar_width = 100
        self.scrollbar_height = 20
        self.scrollbar_pressed = False
        self.scrollbar_mult = 0
        self.engine = None
        self.end_after = end_after
        self.display_needed = display_needed

    def load_pedestrian_spawn_points(self):
        with open("map/people_spawn_points0.txt") as f:
            n = int(f.readline())
            for _ in range(n):
                args = f.readline().split(" ")
                crossing = Engine.PedestrianCrossing(width_range=(int(args[0]), int(args[1])),
                                                     up_spawn_range=(int(args[2]), int(args[3])),
                                                     down_spawn_range=(int(args[4]), int(args[5])),
                                                     type=int(args[6]),
                                                     spawn_prob=int(args[7]))
                self.pedestrian_areas.append(crossing)

    def init_map(self):
        with open("map/map0", "r") as f:
            w, h, n = [int(x) for x in next(f).split()]
            self.map_h, self.map_w = h, w
            for _ in range(w + 1):
                self.map.append([0 for _ in range(h + 1)])
            for _ in range(n):
                x0, y0, x1, y1, t = [int(x) for x in next(f).split()]
                for i in range(x0, x1 + 1):
                    for j in range(y0, y1 + 1):
                        self.map[i][j] = t

    def create_legend(self):
        spacing = 270
        elems_in_col = 5
        counter = [10, 10]
        for label in self.legend_labels:
            self.legend_elems.append(self.font.render(label, True, (0, 0, 0)))
            self.sub_screen.blit(self.legend_elems[-1], counter)
            counter[1] += 30
            if counter[1] > (elems_in_col + 1) * 30:
                counter[0] += spacing
                counter[1] = 40
        for i in range(1, len(self.legend_elems)):
            pygame.draw.rect(self.sub_screen, self.colors[i], pygame.Rect(180 + spacing * ((i - 1) // elems_in_col),
                                                                          40 + 30 * ((i - 1) % elems_in_col), 20, 20))

    def create_speed_control(self):
        self.sub_screen.blit(self.font.render("Simulation speed:", True, (0, 0, 0)), [self.speed_cont_x, 10])
        counter = self.speed_cont_x
        for i in self.speed_cont_vals:
            self.sub_screen.blit(self.font.render(str(i), True, (0, 0, 0)), [counter, 70])
            counter += 30

    def create_light_modes(self):
        self.sub_screen.blit(self.font.render("Lights mode:", True, (0, 0, 0)), [self.speed_cont_x, 120])
        counter = self.speed_cont_x
        for label in self.light_modes_labels:
            self.sub_screen.blit(self.font.render(label, True, (0, 0, 0)), [counter, 180])
            self.modes_buttons_cords.append((counter + len(label) * 6, 150))
            counter += len(label) * 12

    def is_click_inside_scrollbar(self, event) -> bool:
        return (
                self.scrollbar_x <= event.pos[0] <= self.scrollbar_x + self.scrollbar_width and
                self.main_window_height - self.scrollbar_height <= event.pos[1] <= self.main_window_height
        )

    def is_click_in_counters_zone(self, event) -> bool:
        n = len(self.speed_cont_vals)
        return self.speed_cont_x <= event.pos[0] <= self.speed_cont_x + n * (n - 1) * self.button_width \
            and self.sub_window_size[1] + 40 <= event.pos[1] <= self.sub_window_size[1] + 40 + self.button_width \
            and (event.pos[0] - self.speed_cont_x) // self.button_width % 2 == 0

    def is_click_in_modes_zone(self, event) -> bool:
        for (x, y) in self.modes_buttons_cords:
            if x <= event.pos[0] <= x + self.button_width and \
                    self.sub_window_size[1] + y <= event.pos[1] <= self.sub_window_size[1] + y + self.button_width:
                return True
        return False

    def start(self):
        self.init_map()
        self.load_pedestrian_spawn_points()
        self.engine = Engine.Engine(self.map, self.pedestrian_areas, self.chosen_mode)
        Engine.RoadVehicle.engine = self.engine
        if self.display_needed:
            self.main_screen = pygame.display.set_mode(self.main_window_size)
            self.sub_screen = pygame.Surface(self.sub_window_size)
            self.sub_screen.fill((255, 255, 255))
            self.create_legend()
            self.create_speed_control()
            self.create_light_modes()
        self.total_width = 2190
        self.scrollbar_mult = (self.total_width - self.main_window_width) / (
                self.main_window_width - self.scrollbar_width)
        self.main_loop()

    def draw_pedestrians(self):
        for area in self.pedestrian_areas:
            for i in range(area.total_width):
                for j in range(area.total_height):
                    if len(area.map[i][j]) != 0:
                        pygame.draw.rect(
                            self.main_screen, self.colors[5],
                            pygame.Rect((i + area.width_range[0] + self.scroll_x) * self.cell_size,
                                        (j + area.up_spawn_range[0]) * self.cell_size, self.cell_size,
                                        self.cell_size)
                        )

    def change_simulation_speed(self, event):
        i = (event.pos[0] - self.speed_cont_x) // self.button_width
        self.chosen_speed = i // 2

    def change_lights_mode(self, event):
        for i in range(len(self.modes_buttons_cords)):
            if self.modes_buttons_cords[i][0] + self.button_width >= event.pos[0]:
                self.chosen_mode = i
                self.engine.change_lights_mod(i)
                return

    def draw_cars(self):
        cars = self.engine.cars
        for i in range(len(cars)):
            for j in range(len(cars[i])):
                if isinstance(cars[i][j], Engine.RoadVehicle):
                    x_be, y_be = cars[i][j].position
                    drawing_range = (cars[i][j].length, cars[i][j].width)
                    if j != 0:
                        x_be = x_be - drawing_range[0]
                        y_be = y_be - drawing_range[1]
                    pygame.draw.rect(self.main_screen, self.colors[4],
                                     pygame.Rect((x_be + self.scroll_x) * self.cell_size, y_be * self.cell_size,
                                                 drawing_range[0] * self.cell_size, drawing_range[1] * self.cell_size))

        def draw_cars_from_list(cars: list, upwards: bool):
            for car in cars:
                x_be, y_be = car.position
                drawing_range = (car.width, car.length)
                if upwards:
                    x_be -= drawing_range[0]
                else:
                    y_be -= drawing_range[1]
                pygame.draw.rect(self.main_screen, self.colors[4],
                                 pygame.Rect((x_be + self.scroll_x) * self.cell_size, y_be * self.cell_size,
                                             drawing_range[0] * self.cell_size, drawing_range[1] * self.cell_size))

        draw_cars_from_list(self.engine.budryka_cars[0], False)
        draw_cars_from_list(self.engine.budryka_cars[1], True)
        draw_cars_from_list(self.engine.kawiory_cars[0], False)
        draw_cars_from_list(self.engine.kawiory_cars[1], True)

    def draw_map(self):
        self.main_screen.fill((0, 0, 0))
        for i in range(self.map_w + 1):
            for j in range(self.map_h + 1):
                pygame.draw.rect(
                    self.main_screen, self.colors[self.map[i][j]],
                    pygame.Rect((i + self.scroll_x) * self.cell_size, j * self.cell_size, self.cell_size,
                                self.cell_size)
                )

    def draw_scrollbar(self):
        self.main_screen.blit(
            self.sub_screen,
            ((self.main_window_width - self.sub_window_width) // 2, self.main_window_height - self.sub_window_height)
        )
        pygame.draw.rect(
            self.main_screen, (0, 0, 0),
            pygame.Rect(self.scrollbar_x, self.main_window_height - self.scrollbar_height, self.scrollbar_width,
                        self.scrollbar_height)
        )

    def draw_square_button(self, x_pos: int, y_pos: int, width: int, contour: int, is_marked=False):
        button_col = (255, 0, 0)
        pygame.draw.rect(self.sub_screen, button_col, pygame.Rect(x_pos, y_pos, width, width))
        pygame.draw.rect(self.sub_screen, (255, 255, 255), pygame.Rect(x_pos + contour, y_pos + contour,
                                                                       width - 2 * contour, width - 2 * contour))
        if is_marked:
            pygame.draw.rect(self.sub_screen, button_col,
                             pygame.Rect(x_pos + contour + 1, y_pos + contour + 1, width - 2 * (contour + 1),
                                         width - 2 * (contour + 1)))

    def draw_speed_control(self):
        x_pos = self.speed_cont_x
        y_pos = 40
        width = self.button_width
        contour = 3
        for i in range(len(self.speed_cont_vals)):
            self.draw_square_button(x_pos, y_pos, width, contour, self.chosen_speed == i)
            x_pos += 2 * width

    def draw_light_modes(self):
        width = self.button_width
        contour = 3
        for i in range(len(self.modes_buttons_cords)):
            self.draw_square_button(self.modes_buttons_cords[i][0], self.modes_buttons_cords[i][1], width, contour,
                                    self.chosen_mode == i)

    def main_loop(self):
        iteration_interval = 1000  # Time between iterations in ms
        elapsed_time = 0
        while True:
            if self.end_after is not None and self.engine.iter_counter >= self.end_after:
                pygame.quit()
                break
            if not self.display_needed:
                self.engine.iteration()
                continue
            delta_time = self.clock.tick()
            elapsed_time += delta_time
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    print(event.pos[0], event.pos[1])
                    if event.button == 1 and self.is_click_inside_scrollbar(event):
                        self.scrollbar_pressed = True
                    elif event.button == 1 and self.is_click_in_counters_zone(event):
                        self.change_simulation_speed(event)
                    elif event.button == 1 and self.is_click_in_modes_zone(event):
                        self.change_lights_mode(event)
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.scrollbar_pressed = False
                if event.type == pygame.MOUSEMOTION:
                    if self.scrollbar_pressed:
                        self.scrollbar_x += event.rel[0]
                        self.scrollbar_x = max(0, self.scrollbar_x)
                        self.scrollbar_x = min(self.main_window_width - self.scrollbar_width, self.scrollbar_x)
                        self.scroll_x = - self.scrollbar_x * self.scrollbar_mult

            self.draw_map()
            self.draw_scrollbar()
            self.draw_speed_control()
            self.draw_light_modes()
            self.draw_pedestrians()
            self.draw_cars()
            if elapsed_time >= iteration_interval // self.speed_cont_vals[self.chosen_speed]:
                self.engine.iteration()
                elapsed_time = 0
            pygame.display.flip()


if __name__ == '__main__':
    my_board = Board()
    my_board.start()
