def load_instance(filename):
    with open(filename, 'r') as instance:
        width = int(instance.readline().strip())
        circuit_num = int(instance.readline().strip())
        circuits = []
        for i in range(circuit_num):
            circuits.append(tuple(int(el) for el in instance.readline().strip().split(" ")))
        return width, circuits