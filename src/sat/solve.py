import time
from itertools import combinations

from z3 import And, Or, Bool, sat, Not, Solver
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
            px, py = self.set_constraints(plate_height)

            solve_time = time.time()
            if self.sol.check() == sat:
                circuits_pos = self.evaluate(px, py)
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

    def set_constraints(self, plate_height):
        # print(self.max_width)
        # Variables
        px = [[Bool(f"px_{i + 1}_{e}") for e in range(0, self.max_width - self.w[i] + 1)] for i in
              range(self.circuits_num)]
        py = [[Bool(f"py_{i + 1}_{f}") for f in range(0, plate_height - self.h[i] + 1)] for i in
              range(self.circuits_num)]

        lr = [[Bool(f"lr_{i + 1}_{j + 1}") for j in range(self.circuits_num)] for i in
              range(self.circuits_num)]
        ud = [[Bool(f"ud_{i + 1}_{j + 1}") for j in range(self.circuits_num)] for i in
              range(self.circuits_num)]

        # print("Px \n", px)
        # print("Py \n", py)
        # print("Lr \n", lr)
        # print("Ud \n", ud)

        # Ensure that all circuit are placed
        for x in px:
            self.sol.add(Or([i for i in x]))

        for y in py:
            self.sol.add(Or([i for i in y]))

        #
        # Order constraint
        for i in range(self.circuits_num):
            # self.sol.add(px[i][-1])
            for j in range(self.max_width - self.w[i]):
                self.sol.add(Or([Not(px[i][j]), px[i][j + 1]]))
            for j in range(plate_height - self.h[i]):
                self.sol.add(Or([Not(py[i][j]), py[i][j + 1]]))

        #
        # Non overlapping
        for i in range(0, self.circuits_num):
            for j in range(0, self.circuits_num):
                if i < j:
                    if len(px[j]) >= self.w[i]:
                        self.sol.add(Or(Not(lr[i][j]), Not(px[j][self.w[i] - 1])))
                    else:
                        self.sol.add(Or(Not(lr[i][j]), Not(px[j][-1])))
                    if len(px[i]) >= self.w[j]:
                        self.sol.add(Or(Not(lr[j][i]), Not(px[i][self.w[j] - 1])))
                    else:
                        self.sol.add(Or(Not(lr[j][i]), Not(px[i][-1])))
                    if len(py[j]) >= self.h[i]:
                        self.sol.add(Or(Not(ud[i][j]), Not(py[j][self.h[i] - 1])))
                    else:
                        self.sol.add(Or(Not(ud[i][j]), Not(py[j][-1])))
                    if len(py[i]) >= self.h[j]:
                        self.sol.add(Or(Not(ud[j][i]), Not(py[i][self.h[j] - 1])))
                    else:
                        self.sol.add(Or(Not(ud[j][i]), Not(py[i][-1])))

                    self.sol.add(Or(lr[i][j], lr[j][i], ud[i][j], ud[j][i]))

                    for e in range(self.max_width - self.w[i]):
                        if len(px[j]) - 1 >= e + self.w[i]:
                            self.sol.add(Or(Not(lr[i][j]), px[i][e], Not(px[j][e + self.w[i]])))
                        if len(px[i]) - 1 >= e + self.w[j]:
                            self.sol.add(Or(Not(lr[j][i]), px[j][e], Not(px[i][e + self.w[j]])))
                    for f in range(plate_height - self.h[j]):
                        if len(py[j]) - 1 >= f + self.h[i]:
                            self.sol.add(Or(Not(ud[i][j]), py[i][f], Not(py[j][f + self.h[i]])))
                        if len(py[i]) - 1 >= f + self.h[j]:
                            self.sol.add(Or(Not(ud[j][i]), py[j][f], Not(py[i][f + self.h[j]])))

        return px, py

    def evaluate(self, px, py):
        m = self.sol.model()

        circuits_pos = []
        xs = []
        ys = []
        for i in range(self.circuits_num):
            for e in range(len(px[i])):
                if str(m.evaluate(px[i][e])) == 'True':
                    xs.append(e)
                    break
            for f in range(len(py[i])):
                if str(m.evaluate(py[i][f])) == 'True':
                    ys.append(f)
                    break

        for i, (x, y) in enumerate(zip(xs, ys)):
            circuits_pos.append((self.w[i], self.h[i], x, y))

        return circuits_pos
