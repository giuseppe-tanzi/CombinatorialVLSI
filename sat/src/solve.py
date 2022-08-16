import itertools
import time
from itertools import combinations

import numpy as np
from z3 import And, Or, Bool, sat, Not, Solver
from utils import write_solution


class SATsolver:

    def __init__(self, timeout=300, rotation=False):
        self.timeout = timeout
        self.rotation = rotation

    def __init__(self, data, rotation, output_dir, timeout):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            if rotation:
                output_dir = "./sat/out/rot_sym"
            else:
                output_dir = "./sat/out/no_rot_sym"
        self.output_dir = output_dir
        self.timeout = timeout

    def solve(self):
        solutions = []
        for d in self.data:
            solution = self.solve_instance(d)
            ins_num = d[0]
            if solution[0]:
                write_solution(self.output_dir, ins_num, solution[0], solution[1])
            else:
                print(print(f'{ins_num})', (None, 0), 0))
            solutions.append((ins_num, solution[0], solution[1]))
        return solutions

    def solve_instance(self, instance):
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        self.w, self.h = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        lower_bound = int(round(sum([self.h[i] * self.w[i] for i in range(self.circuits_num)]) / self.max_width))
        upper_bound = sum(self.h) - min(self.h)

        start_time = time.time()
        try_timeout = self.timeout
        for plate_height in range(lower_bound, upper_bound + 1):
            self.sol = Solver()
            self.sol.set(timeout=self.timeout * 1000)
            if not self.rotation:
                px, py = self.set_constraints(plate_height)
                r = None
            else:
                print("Solving with rotations")
                px, py, r = self.set_constraints_rotation(plate_height)

            solve_time = time.time()
            if self.sol.check() == sat:
                circuits_pos = self.evaluate(px, py, r)
                return ((self.max_width, plate_height), circuits_pos), (time.time() - solve_time)
            else:
                try_timeout = round((self.timeout - (time.time() - start_time)))
                if try_timeout < 0:
                    return None, 0
        return None, 0

    def all_true(self, bool_vars):
        return And(bool_vars)

    def at_most_one(self, bool_vars):
        return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

    def exactly_one(self, bool_vars):
        self.sol.add(self.at_most_one(bool_vars))
        self.sol.add(self.at_least_one(bool_vars))

    def set_constraints(self, plate_height, symmetry_breaking=True):

        # print(self.max_width)
        # Variables
        px = [[Bool(f"px{i + 1}_{x}") for x in range(self.max_width)] for i in range(self.circuits_num)]
        py = [[Bool(f"py{i + 1}_{y}") for y in range(plate_height)] for i in range(self.circuits_num)]

        # Under and left are two matrices representing the fact that the block is below or at the left of another block
        # e.g. under(i,j) represents that block i is below block j. (Same thing for left)
        ud = [[Bool(f"ud_{i + 1}_{j + 1}") if i != j else 0 for j in range(self.circuits_num)] for i in
              range(self.circuits_num)]
        lr = [[Bool(f"lt{i + 1}_{j + 1}") if j != i else 0 for j in range(self.circuits_num)] for i in
              range(self.circuits_num)]

        # Each pair of block cannot overlap
        for i in range(self.circuits_num):
            for j in range(i + 1, self.circuits_num):
                self.sol.add(Or(lr[i][j], lr[j][i], ud[i][j], ud[j][i]))

        # Clauses due to order encoding
        for i in range(self.circuits_num):
            for e in range(self.max_width - self.w[i]):
                self.sol.add(Or(Not(px[i][e]), px[i][e + 1]))

            for f in range(plate_height - self.h[i]):
                self.sol.add(Or(Not(py[i][f]), py[i][f + 1]))

            # Clauses to force the placement of all the circuits
            for e in range(self.max_width - self.w[i], self.max_width):
                self.sol.add(px[i][e])

            for f in range(plate_height - self.h[i], plate_height):
                self.sol.add(py[i][f])

        for i in range(self.circuits_num):
            for j in range(self.circuits_num):
                if i != j:
                    # lr(i,j) -> xj > wi, lower bound for xj
                    self.sol.add(Or(Not(lr[i][j]), Not(px[j][self.w[i] - 1])))
                    # ud(ri,rj)-> yj > hi, lower bound for yj
                    self.sol.add(Or(Not(ud[i][j]), Not(py[j][self.h[i] - 1])))

                    # 3-literals clauses for non overlapping, shown in the paper
                    for e in range(self.max_width - self.w[i]):
                        self.sol.add(Or(Not(lr[i][j]), px[i][e], Not(px[j][e + self.w[i]])))
                    for e in range(self.max_width - self.w[j]):
                        self.sol.add(Or(Not(lr[j][i]), px[j][e], Not(px[i][e + self.w[j]])))

                    for f in range(plate_height - self.h[i]):
                        self.sol.add(Or(Not(ud[i][j]), py[i][f], Not(py[j][f + self.h[i]])))
                    for f in range(plate_height - self.h[j]):
                        self.sol.add(Or(Not(ud[j][i]), py[j][f], Not(py[i][f + self.h[j]])))

        if symmetry_breaking:
            # domain reduction constraint
            for i in range(int(np.floor((self.max_width - self.w[0]) / 2))):
                self.sol.add(Not(px[0][i]))

            for j in range(int(np.floor((plate_height - self.h[0]) / 2))):
                self.sol.add(Not(py[0][j]))

            for rect in range(1, self.circuits_num):
                if self.w[rect] > np.ceil((self.max_width - self.w[0]) / 2):
                    self.sol.add(Not(lr[0][rect]))
                if self.h[rect] > np.ceil((plate_height - self.h[0]) / 2):
                    self.sol.add(Not(ud[0][rect]))

            # Same size rectangles
            for (i, j) in itertools.combinations(range(self.circuits_num), 2):
                if self.w[i] == self.w[j] and self.h[i] == self.h[j]:
                    self.sol.add(Not(lr[j][i]))
                    self.sol.add(Or(Not(ud[j][i]), lr[i][j]))
        return px, py

    def set_constraints_rotation(self, plate_height, symmetry_breaking=True):
        # print(self.max_width)
        # Variables
        px = [[Bool(f"px{i + 1}_{x}") for x in range(self.max_width)] for i in range(self.circuits_num)]
        py = [[Bool(f"py{i + 1}_{y}") for y in range(plate_height)] for i in range(self.circuits_num)]

        # Under and left are two matrices representing the fact that the block is below or at the left of another block
        # e.g. under(i,j) represents that block i is below block j. (Same thing for left)
        ud = [[Bool(f"ud_{i + 1}_{j + 1}") if i != j else 0 for j in range(self.circuits_num)] for i in
              range(self.circuits_num)]
        lr = [[Bool(f"lt{i + 1}_{j + 1}") if j != i else 0 for j in range(self.circuits_num)] for i in
              range(self.circuits_num)]

        r = [Bool(f"r_{i + 1}") for i in range(self.circuits_num)]

        # Each pair of block cannot overlap
        for i in range(self.circuits_num):
            for j in range(i + 1, self.circuits_num):
                self.sol.add(Or(lr[i][j], lr[j][i], ud[i][j], ud[j][i]))

        # Clauses due to order encoding
        for i in range(self.circuits_num):

            if self.h[i] <= self.max_width:
                self.sol.add(
                    Or(And(Not(r[i]), *[Or(Not(px[i][e]), px[i][e + 1]) for e in range(self.max_width - self.w[i])]),
                       And(r[i], *[Or(Not(px[i][e]), px[i][e + 1]) for e in range(self.max_width - self.h[i])])))

                self.sol.add(
                    Or(And(Not(r[i]), *[Or(Not(py[i][f]), py[i][f + 1]) for f in range(plate_height - self.h[i])]),
                       And(r[i], *[Or(Not(py[i][f]), py[i][f + 1]) for f in range(plate_height - self.w[i])])))

                # Implicit clauses also due to order encoding
                self.sol.add(Or(And(Not(r[i]), *[px[i][e] for e in range(self.max_width - self.w[i], self.max_width)]),
                                And(r[i], *[px[i][e] for e in range(self.max_width - self.h[i], self.max_width)])))

                self.sol.add(Or(And(Not(r[i]), *[py[i][f] for f in range(plate_height - self.h[i], plate_height)]),
                                And(r[i], *[py[i][f] for f in range(plate_height - self.w[i], plate_height)])))
            else:
                self.sol.add(Not(r[i]))
                self.sol.add(*[Or(Not(px[i][e]), px[i][e + 1]) for e in range(self.max_width - self.w[i])])
                self.sol.add(*[Or(Not(py[i][f]), py[i][f + 1]) for f in range(self.max_width - self.h[i])])
                # Implicit clauses also due to order encoding
                self.sol.add(*[px[i][e] for e in range(self.max_width - self.w[i], self.max_width)])
                self.sol.add(*[py[i][f] for f in range(self.max_width - self.h[i], plate_height)])

        # Some cases in which rotation is not possible or useful.
        # If the circuit is a square then it's useless to consider also its rotation.
        self.sol.add([Not(r[i]) for i in range(self.circuits_num) if self.w[i] == self.h[i]])
        # If the height of a circuit is higher than the plate's width ==> Rotation is not possible
        self.sol.add([Not(r[i]) for i in range(self.circuits_num) if self.h[i] > self.max_width])
        # If the width of a circuit is higher than the plate's height ==> Rotation is not possible
        self.sol.add([Not(r[i]) for i in range(self.circuits_num) if self.w[i] > plate_height])

        for i in range(self.circuits_num):
            for j in range(self.circuits_num):
                if i != j:
                    if self.h[i] <= self.max_width:
                        self.sol.add(Or(And(Not(r[i]), Or(Not(lr[i][j]), Not(px[j][self.w[i] - 1]))),
                                        And(r[i], Or(Not(lr[i][j]), Not(px[j][self.h[i] - 1])))))

                        # under(ri,rj)-> yj > hi, lower bound for yj
                        self.sol.add(Or(And(Not(r[i]), Or(Not(ud[i][j]), Not(py[j][self.h[i] - 1]))),
                                        And(r[i], Or(Not(ud[i][j]), Not(py[j][self.w[i] - 1])))))

                        # 3-literals clauses for non overlapping, shown in the paper
                        self.sol.add(Or(And(Not(r[i]), *[Or(Not(lr[i][j]), px[i][e], Not(px[j][e + self.w[i]])) for e in
                                                         range(self.max_width - self.w[i])]),
                                        And(r[i], *[Or(Not(lr[i][j]), px[i][e], Not(px[j][e + self.h[i]])) for e in
                                                    range(self.max_width - self.h[i])])))

                        self.sol.add(Or(And(Not(r[j]), *[Or(Not(lr[j][i]), px[j][e], Not(px[i][e + self.w[j]])) for e in
                                                         range(self.max_width - self.w[j])]),
                                        And(r[j], *[Or(Not(lr[j][i]), px[j][e], Not(px[i][e + self.h[j]])) for e in
                                                    range(self.max_width - self.h[j])])))

                        self.sol.add(Or(And(Not(r[i]),
                                            *[Or(Not(ud[i][j]), py[i][f], Not(py[j][f + self.h[i]])) for f in
                                              range(plate_height - self.h[i])]),
                                        And(r[i], *[Or(Not(ud[i][j]), py[i][f], Not(py[j][f + self.w[i]])) for f in
                                                    range(plate_height - self.w[i])])))

                        self.sol.add(Or(And(Not(r[j]),
                                            *[Or(Not(ud[j][i]), py[j][f], Not(py[i][f + self.h[j]])) for f in
                                              range(plate_height - self.h[j])]),
                                        And(r[j], *[Or(Not(ud[j][i]), py[j][f], Not(py[i][f + self.w[j]])) for f in
                                                    range(plate_height - self.w[j])])))

                    else:
                        # lr(i,j) -> xj > wi, lower bound for xj
                        self.sol.add(Or(Not(lr[i][j]), Not(px[j][self.w[i] - 1])))
                        # ud(ri,rj)-> yj > hi, lower bound for yj
                        self.sol.add(Or(Not(ud[i][j]), Not(py[j][self.h[i] - 1])))
                        # 3-literals clauses for non overlapping, shown in the paper
                        self.sol.add(*[Or(Not(lr[i][j]), px[i][e], Not(px[j][e + self.w[i]])) for e in
                                       range(self.max_width - self.w[i])])

                        self.sol.add(*[Or(Not(lr[j][i]), px[j][e], Not(px[i][e + self.w[j]])) for e in
                                       range(self.max_width - self.w[j])])

                        self.sol.add(*[Or(Not(ud[i][j]), py[i][f], Not(py[j][f + self.h[i]])) for f in
                                       range(plate_height - self.h[i])])

                        self.sol.add(*[Or(Not(ud[j][i]), py[j][f], Not(py[i][f + self.h[j]])) for f in
                                       range(plate_height - self.h[j])])

        # Large rectangle constraints from the paper
        for (i, j) in itertools.combinations(range(self.circuits_num), 2):
            if self.w[i] + self.w[j] > self.max_width:
                self.sol.add(Not(lr[i][j]))
                self.sol.add(Not(lr[j][i]))
            if self.h[i] + self.h[j] > plate_height:
                self.sol.add(Not(ud[i][j]))
                self.sol.add(Not(ud[j][i]))

        if symmetry_breaking:
            if self.h[0] <= self.max_width:
                self.sol.add(
                    Or(And(r[0], *[Not(px[0][i]) for i in range(int(np.floor((self.max_width - self.h[0]) / 2)))]),
                       And(Not(r[0]),
                           *[Not(px[0][i]) for i in range(int(np.floor((self.max_width - self.w[0]) / 2)))])))

                self.sol.add(
                    Or(And(r[0], *[Not(py[0][j]) for j in range(int(np.floor((plate_height - self.w[0]) / 2)))]),
                       And(Not(r[0]), *[Not(py[0][j]) for j in range(int(np.floor((plate_height - self.h[0]) / 2)))])))
            else:
                self.sol.add(And(*[Not(px[0][i]) for i in range(int(np.floor((self.max_width - self.w[0]) / 2)))]))
                self.sol.add(And(*[Not(py[0][j]) for j in range(int(np.floor((plate_height - self.h[0]) / 2)))]))

        return px, py, r

    def evaluate(self, px, py, r):
        m = self.sol.model()
        circuits_pos = []
        xs = []
        ys = []
        for i in range(self.circuits_num):
            for e in range(len(px[i])):
                if m.evaluate(px[i][e]):
                    xs.append(e)
                    break
            for f in range(len(py[i])):
                if m.evaluate(py[i][f]):
                    ys.append(f)
                    break

        for i, (x, y) in enumerate(zip(xs, ys)):
            if r and not m.evaluate(r[i]):
                circuits_pos.append((self.w[i], self.h[i], x, y))
            elif r and m.evaluate(r[i]):
                circuits_pos.append((self.h[i], self.w[i], x, y))
            else:
                circuits_pos.append((self.w[i], self.h[i], x, y))

        return circuits_pos
