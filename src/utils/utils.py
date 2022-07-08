import os
from glob import glob

import matplotlib.pyplot as plt
import numpy as np


def write_solution(output_dir, n, solution, stat):
    """Prints the solution to console and write it in a txt file"""
    print(f'{n})', solution, stat)
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.join(output_dir, f"ins_{n}.txt")
    with open(filename, 'w') as sol:
        if solution != None:
            (plate_width, plate_height), circuits_pos = solution
            sol.write("{0} {1}\n".format(plate_width, plate_height))
            sol.write("{0}\n".format(len(circuits_pos)))
            for c in circuits_pos:
                w, h, x, y = c
                sol.write("{0} {1} {2} {3}\n".format(w, h, x, y))

            sol.write("{0}\n".format(stat))


def load_instance(filename):
    """Loads a single instance from txt file
        :returns num_ins : instance number
                 width : max width allowed
                 circuits : array of tuples (w , h) for each circuit
    """
    with open(filename, 'r') as instance:
        num_ins = filename[filename.find("ins-") + 4:filename.find(".txt")]
        width = int(instance.readline().strip())
        circuit_num = int(instance.readline().strip())
        circuits = []
        for i in range(circuit_num):
            circuits.append(tuple(int(el) for el in instance.readline().strip().split(" ")))
        return num_ins, width, circuits


def load_data(num_instance, input_dir):
    """Return an array containing the instances with the relative instance number
    e.g. [1, plate_width, circuits] where circuits is the array of shapes and 1 indicates the first instance"""
    all_instances = glob(os.path.join(input_dir, "*"))
    if num_instance == 0:
        istances = [load_instance(filename=instance_filename) for instance_filename in all_instances]
        istances.sort(key=lambda x: int(x[0]))
        return istances
    else:
        return [load_instance(filename=filename) for filename in all_instances if
                int(filename[filename.find("ins-") + 4:filename.find(".txt")]) == num_instance]


def display_solution(title, sizes_plate, n_circuits, sizes_circuits, pos_circuits):
    """Displays a solution using a plot"""
    fig, ax = plt.subplots()
    cmap = plt.cm.get_cmap('hsv', n_circuits)
    ax = plt.gca()
    plt.title(title)
    if len(pos_circuits) > 0:
        for i in range(n_circuits):
            rect = plt.Rectangle(pos_circuits[i], *sizes_circuits[i], edgecolor="#333", facecolor=cmap(i))
            ax.add_patch(rect)
    ax.set_xlim(0, sizes_plate[0])
    ax.set_ylim(0, sizes_plate[1] + 1)
    ax.set_xticks(range(sizes_plate[0] + 1))
    ax.set_yticks(range(sizes_plate[1] + 1))
    ax.set_xlabel('width_plate')
    ax.set_ylabel('height_plate')

    plt.show()


def plot_times(output_dir):
    """Plot the barplot of the solving times taken from the solved instance results in output_dir"""
    solutions_paths = glob(
        os.path.join(output_dir, "*.txt"))
    times = np.zeros(40)
    for i in range(1, 41):
        for path in solutions_paths:
            if int(path[path.find("ins_") + 4:path.find(".txt")]) == i:
                with open(path, 'r') as f:
                    times[i - 1] = float(f.readlines()[-1])
    plt.bar(x=np.arange(1, len(times) + 1), height=times)
    plt.xlabel('Instance')
    plt.ylabel('Time (s)')
    plt.yscale("log")
    plt.ylim(0, 300)
    plt.savefig(os.path.join(output_dir, "times_plot.png"))
    plt.show()