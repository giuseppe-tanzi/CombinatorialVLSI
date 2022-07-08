import os
import re
import subprocess
import time

import numpy as np

from src.utils.utils import write_solution


class SMTLIBsolver:

    def __init__(self, data, output_dir, rotation=False, timeout=300):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            output_dir = "../data/output_smtlib/"
        self.output_dir = output_dir
        self.input_dir = "smt/input_smtlib/"
        os.makedirs(self.input_dir, exist_ok=True)
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
        self.file = None

    def solve(self):
        solutions = []
        for d in self.data:
            ins_num = d[0]
            solutions.append(self.solve_instance(d, ins_num))
        return solutions

    def solve_instance(self, instance, ins_num):
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        self.w, self.h = ([i for i, _ in self.circuits], [j for _, j in self.circuits])
        self.file = self.input_dir + "instance_" + str(ins_num) + ".smt2"

        solution, spent_time = self.set_smtlib()

        if solution is not None:
            self.parse_solution(solution)
            circuits_pos = self.evaluate()
            write_solution(self.output_dir, ins_num, ((self.max_width, self.plate_height), circuits_pos),
                           spent_time)
            return ins_num, ((self.max_width, self.plate_height), circuits_pos), spent_time
        else:
            write_solution(self.output_dir, ins_num, None, 0)
            return ins_num, None, 0

    def set_smtlib(self):

        lower_bound = sum([self.h[i] * self.w[i] for i in range(self.circuits_num)]) // self.max_width
        upper_bound = sum(self.h) - min(self.h)

        areas_index = np.argsort([self.h[i] * self.w[i] for i in range(self.circuits_num)])
        areas_index = areas_index[::-1]
        # biggests = areas_index[0], areas_index[1]

        self.w = [self.w[areas_index[i]] for i in range(self.circuits_num)]
        self.h = [self.h[areas_index[i]] for i in range(self.circuits_num)]

        for self.plate_height in range(lower_bound, upper_bound):
            lines = []

            lines.append(f"(set-option :timeout {self.timeout * 1000})")
            lines.append("(set-option :smt.threads 4)")
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
            for i in range(self.circuits_num):
                for j in range(0, i):
                    lines.append(f"(assert (or "
                                 f"(<= (+ x_{i} {self.w[i]}) x_{j}) "
                                 f"(<= (+ x_{j} {self.w[j]}) x_{i}) "
                                 f"(<= (+ y_{i} {self.h[i]}) y_{j}) "
                                 f"(<= (+ y_{j} {self.h[j]}) y_{i})))")

                    # Two rectangles with same dimensions
                    lines.append(f"(assert (=> (and (= {self.w[i]} {self.w[j]}) (= {self.h[i]} {self.h[j]}))"
                                 f" (or "
                                 f"(> x_{j} x_{i}) "
                                 f"(and (= x_{j} x_{i}) (>= y_{j} y_{i})))))")

            # # If two rectangles cannot be packed side to side along the x axis
            # lines += [
            #     f"(assert (=> (> (+ {self.w[i]} {self.w[j]}) {self.max_width}) (or (<= (+ y_{i} {self.h[i]}) y_{j}) (<= (+ y_{j} {self.h[j]}) y_{i}))))"
            #     for i in range(self.circuits_num) for j in range(self.circuits_num) if i != j]
            #
            # # If two rectangles cannot be packed one over the other along the y axis
            # lines += [
            #     f"(assert (=> (> (+ {self.h[i]} {self.h[j]}) {self.plate_height}) (or (<= (+ x_{i} {self.w[i]}) x_{j}) (<= (+ x_{j} {self.w[j]}) x_{i}))))"
            #     for i in range(self.circuits_num) for j in range(self.circuits_num) if i != j]

            # # SUM OVER ROWS (CUMULATIVE)
            # for u in range(self.plate_height):
            #     lines.append(
            #         f"(assert (>= {self.max_width} (+ {' '.join([f'(ite (and (<= y_{i} {u}) (< {u} (+ y_{i} {self.h[i]}))) {self.w[i]} 0)' for i in range(self.circuits_num)])})))")
            #
            # # SUM OVER COLUMNS (CUMULATIVE)
            # for u in range(self.max_width):
            #     lines.append(
            #         f"(assert (>= {self.plate_height} (+ {' '.join([f'(ite (and (<= x_{i} {u}) (< {u} (+ x_{i} {self.w[i]}))) {self.h[i]} 0)' for i in range(self.circuits_num)])})))")

            # Result
            lines.append("(check-sat)")
            lines.append(
                f"(get-value ({' '.join([f'x_{i} y_{i}' for i in range(self.circuits_num)])}))")
            lines.append("(exit)")

            with open(self.file, "w") as f:
                for line in lines:
                    f.write(line + "\n")

            # thread = "z3 parallel.enable=true parallel.threads.max=4 solve.z3"
            # thread_process = subprocess.Popen(thread.split(), stdout=subprocess.PIPE)
            # thread_out, _ = thread_process.communicate()
            # print(thread_out)

            bashCommand = f"z3 -smt2 {self.file}"
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            start_time = time.time()
            output, _ = process.communicate()
            time_spent = time.time() - start_time

            solution = output.decode('ascii')
            print(solution)

            if solution.split("\r")[0] == 'sat':
                return solution, time_spent

            if solution.split("\r")[0] != 'sat' or time_spent >= 300:
                return None, time_spent

    def parse_solution(self, solution):
        text = solution.split("\r")
        sat = re.compile(r'sat')
        text = [i for i in text if not sat.match(i)]
        text = [re.sub("\n", '', text[i]) for i in range(len(text))]
        text = [i for i in text if i != '']
        for i in range(len(text)):
            text[i] = re.sub("\(|\)", '', text[i])
            text[i] = text[i].split(" ")
            text[i] = [j for j in text[i] if j != '']

        self.x_positions = [int(text[i][1]) for i in range(self.circuits_num * 2) if i % 2 == 0]
        self.y_positions = [int(text[i][1]) for i in range(self.circuits_num * 2) if i % 2 == 1]

    def evaluate(self):
        return [(self.w[i], self.h[i], self.x_positions[i], self.y_positions[i]) for i in range(self.circuits_num)]
