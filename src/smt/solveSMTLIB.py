import os
import subprocess
import time


class SMTLIBSolver:

    def __init__(self, data, output_dir, rotation=False, timeout=300):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            output_dir = "../data/output_smtlib/"
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.timeout = timeout

        self.circuits_num = None
        self.circuits = None
        self.max_width = None
        self.y_positions = None
        self.x_positions = None
        self.sol = None
        self.h = None
        self.w = None
        self.plate_height = None

    def solve(self):
        for d in self.data:
            ins_num = d[0]
            print(f"Instance num: {ins_num}")
            self.file = self.output_dir + "instance_" + str(ins_num) + ".smt2"
            solution, time = self.solve_instance(d)
            # write_solution(ins_num, solution[0], solution[1])
            print(solution)
            print(f"Time: {time}")
            print(f"Height: {self.plate_height}")
        return None

    def solve_instance(self, instance):
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        self.w, self.h = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        solution, solve_time = self.set_smtlib()

        return solution, solve_time

    def set_smtlib(self):

        lower_bound = sum([self.h[i] * self.w[i] for i in range(self.circuits_num)]) // self.max_width
        upper_bound = sum(self.h) - min(self.h)

        for self.plate_height in range(lower_bound, upper_bound):

            lines = []

            lines.append(f"(set-option :timeout {self.timeout * 1000})")
            lines.append("(set-logic QF_LIA)")

            # Decision Variables
            for i in range(self.circuits_num):
                lines.append(f"(declare-const x_{i} Int)")
                lines.append(f"(declare-const y_{i} Int)")

            # lines.append("(declare-fun x (Int) Int)")
            # lines.append("(declare-fun y (Int) Int)")

            # Domain
            lines += [f"(assert (and (>= x_{i} 0) (<= x_{i} (- {self.max_width} {self.w[i]}))))" for i
                      in
                      range(self.circuits_num)]
            lines += [f"(assert (and (>= y_{i} 0) (<= y_{i} (- {self.plate_height} {self.h[i]}))))"
                      for i in
                      range(self.circuits_num)]

            # Constraints

            # DO NOT OVERLAP
            lines += [f"(assert (or "
                      f"(<= (+ x_{i} {self.w[i]}) x_{j}) "
                      f"(<= (+ x_{j} {self.w[j]}) x_{i}) "
                      f"(<= (+ y_{i} {self.h[i]}) y_{j}) "
                      f"(<= (+ x_{j} {self.h[j]}) y_{i})))" for i in range(1, self.circuits_num) for j
                      in range(0, i)]

            # Two rectangles with same dimensions
            lines += [f"(assert (=> (and (= {self.w[i]} {self.w[j]}) (= {self.h[i]} {self.h[j]}))"
                      f" (or "
                      f"(> x_{j} x_{i}) "
                      f"(and (= x_{j} x_{i}) (>= y_{j} y_{i})))))"
                      for i in range(self.circuits_num) for j in
                      range(self.circuits_num)
                      if i != j]

            # If two rectangles cannot be packed side to side along the x axis
            lines += [
                f"(assert (=> (> (+ {self.w[i]} {self.w[j]}) {self.max_width}) (or (<= (+ y_{i} {self.h[i]}) y_{j}) (<= (+ y_{j} {self.h[j]}) y_{i}))))"
                for i in range(self.circuits_num) for j in range(self.circuits_num) if i != j]

            # If two rectangles cannot be packed one over the other along the y axis
            lines += [
                f"(assert (=> (> (+ {self.h[i]} {self.h[j]}) {self.plate_height}) (or (<= (+ x_{i} {self.w[i]}) x_{j}) (<= (+ x_{j} {self.w[j]}) x_{i}))))"
                for i in range(self.circuits_num) for j in range(self.circuits_num) if i != j]

            # SUM OVER ROWS (CUMULATIVE)
            for u in range(self.plate_height):
                lines.append(
                    f"(assert (>= {self.max_width} (+ {' '.join([f'(ite (and (<= y_{i} {u}) (< {u} (+ y_{i} {self.h[i]}))) {self.w[i]} 0)' for i in range(self.circuits_num)])})))")

            # SUM OVER COLUMNS (CUMULATIVE)
            for u in range(self.max_width):
                lines.append(
                    f"(assert (>= {self.plate_height} (+ {' '.join([f'(ite (and (<= x_{i} {u}) (< {u} (+ x_{i} {self.w[i]}))) {self.h[i]} 0)' for i in range(self.circuits_num)])})))")

            # Result
            lines.append("(check-sat)")
            lines.append(
                f"(get-value ({' '.join([f'x_{i} y_{i}' for i in range(self.circuits_num)])}))")
            lines.append("(exit)")

            with open(self.file, "w") as f:
                for line in lines:
                    f.write(line + "\n")

            bashCommand = f"z3 -smt2 {self.file}"
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            start_time = time.time()
            output, _ = process.communicate()
            time_spent = time.time() - start_time

            solution = output.decode('ascii')

            if solution.split("\r")[0] == 'sat' or time_spent > 300:
                break

        return solution, time_spent
