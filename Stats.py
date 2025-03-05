import os
import shutil
from Board import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def draw_charts():
    light_modes_labels = ["Original", "Crossing synch", "Time loop", "No lights"]
    for i in range(4):
        df = pd.read_csv(f"res/stats{i}.csv")
        df = df.iloc[7:]
        init_iter, init_cars, init_time_cars, init_pedestrians, init_time_pedestrians = df.iloc[0]
        tmp = np.empty(len(df.iloc[:, 0].to_numpy()))
        tmp.fill(init_iter)
        x = df.iloc[:, 0].to_numpy() - tmp
        tmp.fill(init_cars)
        cars_num = df.iloc[:, 1].to_numpy() - tmp
        tmp.fill(init_time_cars)
        cars_time = df.iloc[:, 2].to_numpy() - tmp
        tmp.fill(init_pedestrians)
        pedestrians_num = df.iloc[:, 3].to_numpy() - tmp
        tmp.fill(init_time_pedestrians)
        pedestrians_time = df.iloc[:, 4].to_numpy() - tmp
        fig, ax = plt.subplots()
        ax.plot(x[1:], [cars_time[j] / cars_num[j] if cars_num[j] != 0 else 0 for j in range(1, len(cars_num))],
                label="Average waiting time for car")
        ax.plot(x[1:], [pedestrians_time[j] / pedestrians_num[j] if pedestrians_num[j] != 0 else 0
                        for j in range(1, len(pedestrians_num))], label="Average waiting time for pedestrian", c="red")
        ax.grid()
        ax.legend()
        ax.set_title(f"Average waiting times for two groups\non the pedestrian crossing - {light_modes_labels[i]} mode")
        ax.set_xlabel("Time in simulation [s]")
        ax.set_ylabel("Average waiting time [s]")
        fig.show()
        fig.savefig(f"res/{light_modes_labels[i]}.png")
        a = 5


def get_data():
    for i in range(4):
        my_board = Board(initial_lights_mode=i, initial_simulation_speed=8, end_after=1121, display_needed=False)
        my_board.start()
        new_name = f"stats{i}.csv"
        os.rename("stats.csv", new_name)
        shutil.move(new_name, "./res")


def remove_current_res():
    for file in os.listdir("res"):
        os.remove(f"res/{file}")


if __name__ == '__main__':
    remove_current_res()
    get_data()
    draw_charts()
