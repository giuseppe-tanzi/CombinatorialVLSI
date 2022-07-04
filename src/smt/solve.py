import time

from z3 import And, Or, sat, Solver, Sum, If, IntVector


class SMTsolver:

    def __init__(self, data, output_dir, rotation=False, timeout=300):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            output_dir = "../data/output_sat/"
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
        for d in self.data:
            solution = self.solve_instance(d)
            ins_num = d[0]
            print(f"Instance num: {ins_num}")
            # write_solution(ins_num, solution[0], solution[1])
            print(solution)
        return None

    def solve_instance(self, instance):
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        self.w = IntVector('widths', self.circuits_num)
        self.h = IntVector('heights', self.circuits_num)

        for i in range(self.circuits_num):
            self.w[i], _ = self.circuits[i]
            _, self.h[i] = self.circuits[i]

        #        self.w, self.h = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        lower_bound = sum([self.h[i] * self.w[i] for i in range(self.circuits_num)]) // self.max_width
        upper_bound = sum(self.h) - min(self.h)

        start_time = time.time()
        try_timeout = self.timeout
        for plate_height in range(lower_bound, upper_bound + 1):
            self.sol = Solver()
            self.sol.set(timeout=self.timeout * 1000)
            #            plate, rotations = self.set_constraints(plate_height)
            self.set_constraints(plate_height)

            solve_time = time.time()
            if self.sol.check() == sat:
                circuits_pos = self.evaluate()
                return ((self.max_width, plate_height), circuits_pos), (time.time() - solve_time)
            else:
                try_timeout = round((self.timeout - (time.time() - start_time)))
                if try_timeout < 0:
                    return None, 0
        return None, 0

    def set_constraints(self, plate_height):

        self.x_positions = IntVector('x_pos', self.circuits_num)
        self.y_positions = IntVector('y_pos', self.circuits_num)

        # CONSTRAINTS

        # NOT EXCEED, DOMAINS
        self.sol.add([And(0 <= self.x_positions[i], self.x_positions[i] <= self.max_width - self.w[i])
                      for i in range(self.circuits_num)])

        self.sol.add([And(0 <= self.y_positions[i], self.y_positions[i] <= plate_height - self.h[i])
                      for i in range(self.circuits_num)])

        # DO NOT OVERLAP
        for i in range(1, self.circuits_num):
            for j in range(0, i):
                self.sol.add(Or(self.y_positions[i] + self.h[i] <= self.y_positions[j],
                                self.y_positions[j] + self.h[j] <= self.y_positions[i],
                                self.x_positions[i] + self.w[i] <= self.x_positions[j],
                                self.x_positions[j] + self.w[j] <= self.x_positions[i]))

        # SUM OVER ROWS (CUMULATIVE)
        for u in range(plate_height):
            self.sol.add(
                self.max_width >= Sum([If(And(self.y_positions[i] <= u, u < self.y_positions[i] + self.h[i]),
                                          self.w[i], 0) for i in range(self.circuits_num)]))

        # SUM OVER COLUMNS (CUMULATIVE)
        for u in range(self.max_width):
            self.sol.add(plate_height >= Sum([If(And(self.x_positions[i] <= u, u < self.x_positions[i] + self.w[i]),
                                                 self.h[i], 0) for i in range(self.circuits_num)]))

    def evaluate(self):
        return [[int(self.sol.model().evaluate(self.x_positions[i]).as_string()),
                 int(self.sol.model().evaluate(self.y_positions[i]).as_string())] for i in range(self.circuits_num)]
