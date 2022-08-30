import time

import numpy as np
from z3 import And, Or, sat, Sum, IntVector, Tactic, Implies, If

from utils import write_solution


class SMTsolver:

    def __init__(self, data, output_dir, timeout):
        self.data = data
        if output_dir == "":
            output_dir = "./smt/out/no_rot"
        self.output_dir = output_dir
        self.timeout = timeout

        self.circuits_num = None
        self.circuits = None
        self.max_width = None
        self.y_positions = None
        self.x_positions = None
        self.sol = None
        self.h = None
        self.w = None

    def solve(self):
        solutions = []
        for d in self.data:
            ins_num = d[0]
            solutions.append(self.solve_instance(d, ins_num))
        return solutions

    def solve_instance(self, instance, ins_num):
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)
        self.w = IntVector('widths', self.circuits_num)
        self.h = IntVector('heights', self.circuits_num)

        for i in range(self.circuits_num):
            self.w[i], _ = self.circuits[i]
            _, self.h[i] = self.circuits[i]

        lower_bound = sum([self.h[i] * self.w[i] for i in range(self.circuits_num)]) // self.max_width
        upper_bound = sum(self.h) - min(self.h)

        for plate_height in range(lower_bound, upper_bound + 1):
            self.sol = Tactic('auflia').solver()
            self.sol.set(timeout=self.timeout * 1000)
            self.sol.set(threads=8)

            self.set_constraints(plate_height, self.w, self.h)

            solve_time = time.time()
            if self.sol.check() == sat:
                spent_time = time.time() - solve_time
                circuits_pos = self.evaluate()
                write_solution(self.output_dir, ins_num, ((self.max_width, plate_height), circuits_pos),
                               spent_time)
                return ins_num, ((self.max_width, plate_height), circuits_pos), spent_time
            else:
                try_timeout = round((self.timeout - (time.time() - solve_time)))
                if try_timeout <= 0:
                    write_solution(self.output_dir, ins_num, None, 0)
                    return ins_num, None, 0
        return ins_num, None, 0

    def set_constraints(self, plate_height, widths, heights):

        self.x_positions = IntVector('x_pos', self.circuits_num)
        self.y_positions = IntVector('y_pos', self.circuits_num)

        areas_index = np.argsort([self.h[i] * self.w[i] for i in range(self.circuits_num)])
        areas_index = areas_index[::-1]
        biggests = areas_index[0], areas_index[1]

        # Constraints

        # Domains
        self.sol.add([And(0 <= self.x_positions[i], self.x_positions[i] <= self.max_width - self.w[i])
                      for i in range(self.circuits_num)])

        self.sol.add([And(0 <= self.y_positions[i], self.y_positions[i] <= plate_height - self.h[i])
                      for i in range(self.circuits_num)])

        for i in range(1, self.circuits_num):
            for j in range(0, i):
                # No Overlapping
                self.sol.add(Or(Sum(self.y_positions[i], self.h[i]) <= self.y_positions[j],
                                Sum(self.y_positions[j], self.h[j]) <= self.y_positions[i],
                                Sum(self.x_positions[i], self.w[i]) <= self.x_positions[j],
                                Sum(self.x_positions[j], self.w[j]) <= self.x_positions[i]))

                # Symmetry breaking: two rectangles with same dimensions
                self.sol.add(Implies(And(self.w[i] == self.w[j], self.h[i] == self.h[j]),
                                     Or(self.x_positions[j] > self.x_positions[i],
                                        And(self.x_positions[j] == self.x_positions[i],
                                            self.y_positions[j] >= self.y_positions[i]))))

        # Symmetry breaking : fix relative position of the two biggest rectangles
        self.sol.add(Or(self.x_positions[biggests[1]] > self.x_positions[biggests[0]],
                        And(self.x_positions[biggests[1]] == self.x_positions[biggests[0]],
                            self.y_positions[biggests[1]] >= self.y_positions[biggests[0]])))

        # Cumulative over columns
        for u in range(self.max_width):
            self.sol.add(plate_height >= Sum([If(And(self.x_positions[i] <= u, u < Sum(self.x_positions[i], self.w[i])),
                                                 self.h[i], 0) for i in range(self.circuits_num)]))

    def evaluate(self):
        x = [int(self.sol.model().evaluate(self.x_positions[i]).as_string()) for i in range(self.circuits_num)]
        y = [int(self.sol.model().evaluate(self.y_positions[i]).as_string()) for i in range(self.circuits_num)]

        return [(self.w[i], self.h[i], x[i], y[i]) for i in range(self.circuits_num)]
