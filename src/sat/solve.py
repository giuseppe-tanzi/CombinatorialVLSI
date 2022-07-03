import os
import time
from z3 import And, Or, Bool, sat, Not, Solver, Implies
from itertools import combinations

from utils.utils import write_solution


class SATsolver:

    def __init__(self, timeout=300, rotation=False):
        self.timeout = timeout
        self.rotation = rotation

    def __init__(self, data, rotation, output_dir, timeout):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            output_dir = "../data/output_sat/"
        self.output_dir = output_dir
        self.timeout = timeout

    def solve(self):
        for d in self.data:
            solution = self.solve_instance(d)
            ins_num = d[0]
            # write_solution(ins_num, solution[0], solution[1])
            print(solution)
        return None

    def solve_instance(self, instance):
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        self.w, self.h = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        lower_bound = sum([self.h[i] * self.w[i] for i in range(self.circuits_num)]) // self.max_width
        upper_bound = sum(self.h) - min(self.h)

        start_time = time.time()
        try_timeout = self.timeout
        for plate_height in range(lower_bound, upper_bound + 1):
            self.sol = Solver()
            self.sol.set(timeout=self.timeout * 1000)
            plate, rotations = self.set_constraints(plate_height)

            solve_time = time.time()
            if self.sol.check() == sat:
                circuits_pos = self.evaluate(plate_height, plate, rotations)
                return ((self.max_width, plate_height), circuits_pos), (time.time() - solve_time)
            else:
                try_timeout = round((self.timeout - (time.time() - start_time)))
                if try_timeout < 0:
                    return None, 0
        return None, 0

    def all_true(self, bool_vars):
        return And(bool_vars)

    def at_least_one(self, bool_vars):
        return Or(bool_vars)

    def at_most_one(self, bool_vars):
        return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

    def exactly_one(self, bool_vars):
        self.sol.add(self.at_most_one(bool_vars))
        self.sol.add(self.at_least_one(bool_vars))

    def set_constraints(self, plate_height):
        # First model
        plate = [[[Bool(f"b_{i}_{j}_{k}") for k in range(self.circuits_num)] for j in range(plate_height)] for i in
                 range(self.max_width)]
        rotations = None

        # Second model
        xs = [[Bool(f"x_{i}_{j}") for j in range(self.circuits_num)] for i in range(self.max_width)]
        ys = [[Bool(f"y_{i}_{j}") for j in range(self.circuits_num)] for i in range(plate_height)]

        # Channelling constraint
        for k in range(self.circuits_num):
            for y in range(plate_height):
                p = self.at_least_one([plate[x][y][k] for x in range(self.max_width)])
                self.sol.add(And(Implies(ys[y][k], p), Implies(p, ys[y][k])))
            for x in range(self.max_width):
                p = self.at_least_one([plate[x][y][k] for y in range(plate_height)])
                self.sol.add(And(Implies(xs[x][k], p), Implies(p, xs[x][k])))

        if not self.rotation:
            for k in range(self.circuits_num):
                configurations = []
                # TODO : si può fare come list comprehension
                for y in range(plate_height - self.h[k] + 1):
                    for x in range(self.max_width - self.w[k] + 1):
                        configurations.append(self.all_true(
                            [plate[x + xk][y + yk][k] for yk in range(self.h[k]) for xk in range(self.w[k])]))

                self.exactly_one(configurations)
        else:
            rotations = [Bool(f"r_{k}") for k in range(self.circuits_num)]
            for k in range(self.circuits_num):
                min_dim = min(self.h[k], self.w[k])

                configurations = []
                configurations_r = []
                for y in range(plate_height - min_dim + 1):
                    for x in range(self.max_width - min_dim + 1):
                        conf1 = []
                        conf2 = []

                        for yk in range(self.h[k]):
                            for xk in range(self.w[k]):
                                if y + self.h[k] <= plate_height and x + self.w[k] <= self.max_width:
                                    conf1.append(plate[x + xk][y + yk][k])
                                if y + self.w[k] <= plate_height and x + self.h[k] <= self.max_width:
                                    conf2.append(plate[x + yk][y + xk][k])

                        if len(conf1) > 0:
                            configurations.append(self.all_true(conf1))

                        if len(conf2) > 0:
                            configurations_r.append(self.all_true(conf2))

                if len(configurations) > 0 and len(configurations_r) > 0:
                    self.exactly_one([
                        And(self.at_least_one(configurations), Not(rotations[k])),
                        And(self.at_least_one(configurations_r), rotations[k])
                    ])
                elif len(configurations) > 0:
                    self.sol.add(And(self.at_least_one(configurations), Not(rotations[k])))
                elif len(configurations_r) > 0:
                    self.sol.add(And(self.at_least_one(configurations_r), rotations[k]))

        # Non-overlapping constraint
        for x in range(self.max_width):
            for y in range(plate_height):
                self.sol.add(self.at_most_one([plate[x][y][k] for k in range(self.circuits_num)]))

        prev = []
        flat_x = [xs[x][k] for x in range(self.max_width) for k in range(self.circuits_num)]
        flat_x_r = [xs[self.max_width - x - 1][k] for x in range(self.max_width) for k in range(self.circuits_num)]
        for x in range(len(flat_x)):
            if len(prev) > 0:
                self.sol.add(Implies(And(prev), Implies(flat_x[x], flat_x_r[x])))
            else:
                self.sol.add(Implies(flat_x[x], flat_x_r[x]))
            prev.append(And(Implies(flat_x[x], flat_x_r[x]), Implies(flat_x_r[x], flat_x[x])))

        prev = []
        flat_y = [ys[y][k] for y in range(plate_height) for k in range(self.circuits_num)]
        flat_y_r = [ys[plate_height - y - 1][k] for y in range(plate_height) for k in range(self.circuits_num)]
        for y in range(len(flat_y)):
            if len(prev) > 0:
                self.sol.add(Implies(And(prev), Implies(flat_y[y], flat_y_r[y])))
            else:
                self.sol.add(Implies(flat_x[y], flat_x_r[y]))

            prev.append(And(Implies(flat_y[y], flat_y_r[y]), Implies(flat_y_r[y], flat_y[y])))

        return plate, rotations

    def evaluate(self, plate_height, plate, rotations):
        m = self.sol.model()

        circuits_pos = []
        for k in range(self.circuits_num):
            found = False
            for x in range(self.max_width):
                if found:
                    break
                for y in range(plate_height):
                    if not found and m.evaluate(plate[x][y][k]):
                        if not self.rotation:
                            circuits_pos.append((self.w[k], self.h[k], x, y))
                        else:
                            if m.evaluate(rotations[k]):
                                circuits_pos.append((self.h[k], self.w[k], x, y))
                            else:
                                circuits_pos.append((self.w[k], self.h[k], x, y))
                        found = True
                    elif found:
                        break

        return circuits_pos
