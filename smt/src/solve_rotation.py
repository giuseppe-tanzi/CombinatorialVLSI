import time

import numpy as np
from z3 import IntVector, Tactic, sat, BoolVector, If, And, Not, Or, Sum

from smt.src.solve import SMTsolver
from utils import write_solution


class SMTsolverRot(SMTsolver):

    def __init__(self, data, output_dir, timeout):
        super().__init__(data, output_dir, timeout)
        if output_dir == "":
            output_dir = "./smt/out/rot"
        self.output_dir = output_dir

    def solve_instance(self, instance, ins_num):
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)
        self.w = IntVector('widths', self.circuits_num)
        self.h = IntVector('heights', self.circuits_num)

        widths, heights = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        lower_bound = sum([heights[i] * widths[i] for i in range(self.circuits_num)]) // self.max_width
        upper_bound = sum(heights) - min(heights)

        for plate_height in range(lower_bound, upper_bound + 1):
            self.sol = Tactic('auflia').solver()
            self.sol.set(timeout=self.timeout * 1000)
            self.sol.set(threads=4)

            self.set_constraints(plate_height, widths, heights)

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

        areas_index = np.argsort([heights[i] * widths[i] for i in range(self.circuits_num)])
        areas_index = areas_index[::-1]
        biggests = areas_index[0], areas_index[1]
        widths = [widths[areas_index[i]] for i in range(self.circuits_num)]
        heights = [heights[areas_index[i]] for i in range(self.circuits_num)]

        # Handling rotation
        rotations = BoolVector('rotations', self.circuits_num)
        for i in range(self.circuits_num):
            self.sol.add(If(rotations[i], And(widths[i] == self.h[i], heights[i] == self.w[i]),
                            And(widths[i] == self.w[i], heights[i] == self.h[i])))
            self.sol.add(If(widths[i] == heights[i], Not(rotations[i]), Or(rotations[i], Not(rotations[i]))))

        # CONSTRAINTS

        # Domains
        self.sol.add([And(0 <= self.x_positions[i], self.x_positions[i] <= self.max_width - self.w[i])
                      for i in range(self.circuits_num)])

        self.sol.add([And(0 <= self.y_positions[i], self.y_positions[i] <= plate_height - self.h[i])
                      for i in range(self.circuits_num)])

        for i in range(1, self.circuits_num):
            for j in range(0, i):
                # Don't overlap
                self.sol.add(Or(Sum(self.y_positions[i], self.h[i]) <= self.y_positions[j],
                                Sum(self.y_positions[j], self.h[j]) <= self.y_positions[i],
                                Sum(self.x_positions[i], self.w[i]) <= self.x_positions[j],
                                Sum(self.x_positions[j], self.w[j]) <= self.x_positions[i]))

        # Symmetry breaking : fix relative position of the two biggest rectangles
        self.sol.add(Or(self.x_positions[biggests[1]] > self.x_positions[biggests[0]],
                        And(self.x_positions[biggests[1]] == self.x_positions[biggests[0]],
                            self.y_positions[biggests[1]] >= self.y_positions[biggests[0]])))

        # Cumulative over rows
        for u in range(plate_height):
            self.sol.add(
                self.max_width >= Sum([If(And(self.y_positions[i] <= u, u < Sum(self.y_positions[i], self.h[i])),
                                          self.w[i], 0) for i in range(self.circuits_num)]))

    def evaluate(self):
        widths = [int(self.sol.model().evaluate(self.w[i]).as_string()) for i in range(self.circuits_num)]
        heights = [int(self.sol.model().evaluate(self.h[i]).as_string()) for i in range(self.circuits_num)]
        x = [int(self.sol.model().evaluate(self.x_positions[i]).as_string()) for i in range(self.circuits_num)]
        y = [int(self.sol.model().evaluate(self.y_positions[i]).as_string()) for i in range(self.circuits_num)]

        return [(widths[i], heights[i], x[i], y[i]) for i in range(self.circuits_num)]
