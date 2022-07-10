from utils import write_solution
from ortools.linear_solver import pywraplp
import time
import numpy as np


class LPsolver:

    def __init__(self, data, rotation, output_dir, timeout):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            output_dir = "../../data/output_lp/"
        self.output_dir = output_dir
        self.timeout = timeout
        self.ins_num = None

    def solve(self):
        solutions = []
        for d in self.data:
            self.ins_num = d[0]
            solution = self.solve_instance(d)
            solutions.append(solution)
            # write_solution(ins_num, solution[0], solution[1])
        return solutions

    def valid_positions(self, c_w, c_h, max_width, max_h):
        val_pos = []
        for i in range(max_width):
            for j in range(max_h):
                if i + c_w <= max_width and j + c_h <= max_h:
                    create_binary_encoding = np.zeros(max_h * max_width)
                    for k in range(j, j + c_h):
                        create_binary_encoding[k * max_width + i: k * max_width + i + c_w] = 1
                    val_pos.append(create_binary_encoding)
        return val_pos

    def solve_instance(self, instance):
        start = time.time()
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        widths, heights = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        lower_bound = sum([heights[i] * widths[i] for i in range(self.circuits_num)]) // self.max_width
        upper_bound = sum(heights) - min(heights)

        for max_h in range(lower_bound, upper_bound + 1):

            # creating the tensor which contains, for each circuit, all its possible valid positions
            C = [self.valid_positions(widths[i], heights[i], self.max_width, max_h) for i in range(self.circuits_num)]

            # creating the model
            solver = pywraplp.Solver.CreateSolver('SCIP')
            solver.SetTimeLimit(self.timeout * 1000)
            # solver.EnableOutput()
            # solver.SetNumThreads(8)

            # X contiene, per ogni circuito, un numero di liste pari al numero di posizioni valide che il circuito
            # può ricoprire nella plate di dimensioni max_width * current_h (lower_bound)
            X = []
            start_2 = time.time()
            for i in range(self.circuits_num):
                X.append([solver.IntVar(lb=0, ub=1, name=f'x_{i}_{j}') for j in range(len(C[i]))])
            print('First cycle time: ', time.time() - start_2)

            # no overlapping
            # ogni posizione p sulla plate non deve essere occupata da più di 1 circuito
            start_3 = time.time()
            print('Number of constraints: ', np.array(C[0]).shape[1])
            solver.Add(
                sum([C[i][j][k] * X[i][j] for i in range(self.circuits_num) for j in range(len(C[i])) for r in range(max_h) for k in
                     range(r * self.max_width, r * self.max_width + self.max_width)]) <= (
                            self.max_width * max_h))
            print('Second cycle time: ', time.time() - start_3)

            # ogni circuito deve essere piazzato esattamente una volta
            start_4 = time.time()
            for i in range(self.circuits_num):
                solver.Add(sum([X[i][j] for j in range(len(C[i]))]) == 1)
            print('Third cycle time: ', time.time() - start_4)

            print('Instantiation time: ', (time.time() - start))
            status = solver.Solve()
            total_time = solver.WallTime() / 1000
            print('Total time elapsed: ', total_time)

            if status == pywraplp.Solver.OPTIMAL:
                circuit_pos = []
                for i in range(self.circuits_num):
                    for j in range(len(C[i])):
                        if X[i][j].solution_value() > 0:
                            indexes = np.where((np.array(C[i][j]).reshape((self.max_width, max_h))) == 1)
                    circuit_pos.append((widths[i], heights[i], indexes[1][0], indexes[0][0]))

                # self.print_solution(C, X, max_h)
                write_solution(self.output_dir, self.ins_num, ((self.max_width, max_h), circuit_pos), total_time)
                return self.ins_num, ((self.max_width, max_h), circuit_pos), total_time

    def print_solution(self, C, X, max_h):
        representation = np.zeros((self.max_width, max_h))
        for i in range(self.circuits_num):
            for j in range(len(C[i])):
                if X[i][j].solution_value() > 0:
                    representation += np.array(C[i][j]).reshape((self.max_width, max_h))
        print("H :", max_h)
        print(representation)
