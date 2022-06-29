from glob import glob
import os


def write_solution(n, solution, stat):
    # TODO : Scrivere la parte di salvataggio su file di questi risultati.
    print(solution, stat)


def load_instance(filename):
    with open(filename, 'r') as instance:
        num_ins = filename[filename.find("ins-") + 4:filename.find(".txt")]
        width = int(instance.readline().strip())
        circuit_num = int(instance.readline().strip())
        circuits = []
        for i in range(circuit_num):
            circuits.append(tuple(int(el) for el in instance.readline().strip().split(" ")))
        return num_ins, width, circuits


def load_data(num_instances, input_dir):
    """Return an array containing the instances with the relative instance number
    e.g. [1, plate_width, circuits] where circuits is the array of shapes and 1 indicates the first instance"""
    all_instances = glob(os.path.join(input_dir, "*"))
    if num_instances == 0:
        return [load_instance(filename=instance_filename) for instance_filename in all_instances]
    else:
        return [load_instance(filename=filename) for filename in all_instances if
                int(filename[filename.find("ins-") + 4:filename.find(".txt")]) == num_instances]
