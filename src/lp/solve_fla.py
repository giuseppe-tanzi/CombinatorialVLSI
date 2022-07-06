import time

import numpy as np
from ortools.linear_solver import pywraplp
from utils.utils import write_solution


class LPsolver:

    def __init__(self, data, rotation, output_dir, timeout):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            output_dir = "../data/output_lp/"
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

    def solve_instance(self, instance):
        start = time.time()
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        widths, heights = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        lower_bound = sum([heights[i] * widths[i] for i in range(self.circuits_num)]) // self.max_width
        upper_bound = sum(heights) - min(heights)

        for max_h in range(lower_bound, upper_bound + 1):

            # creating the model
            solver = pywraplp.Solver.CreateSolver('SCIP')
            solver.SetTimeLimit(self.timeout * 1000)
            # solver.EnableOutput()
            solver.SetNumThreads(6)

            max_x = self.max_width - min(widths)
            max_y = max_h - min(heights)

            x = []
            y = []
            for i in range(self.circuits_num):
                x.append(solver.IntVar(lb=0, ub=max_x, name=f'x_{i}'))
                y.append(solver.IntVar(lb=0, ub=max_y, name=f'y_{i}'))

            # disjunction bool variables
            d = [
                [[solver.IntVar(lb=0, ub=1, name=f'd_{i}_{j}_{k}') for k in range(4)] for j in range(self.circuits_num)]
                for i in range(self.circuits_num)]
            M = 1000
            for i in range(self.circuits_num):
                # basic constraints of containment
                solver.Add(x[i] + widths[i] <= self.max_width)
                solver.Add(y[i] + heights[i] <= max_h)
                # non overlapping constraints
                for j in range(i + 1, self.circuits_num):
                    solver.Add(sum(d[i][j]) == 1)
                    solver.Add(x[i] + widths[i] <= x[j] + M * (1 - d[i][j][0]))
                    solver.Add(x[j] + widths[j] <= x[i] + M * (1 - d[i][j][1]))
                    solver.Add(y[i] + heights[i] <= y[j] + M * (1 - d[i][j][2]))
                    solver.Add(y[j] + heights[j] <= y[i] + M * (1 - d[i][j][3]))

            # cumulative constraint over rows
            c_w = [[solver.IntVar(lb=0, ub=max(widths), name=f'a_{i}_{u}') for u in range(max_h)] for i in
                   range(self.circuits_num)]
            delta = [[solver.IntVar(lb=0, ub=1, name=f'delta_{i}_{u}') for u in range(max_h)] for i in
                     range(self.circuits_num)]
            delta2 = [[solver.IntVar(lb=0, ub=1, name=f'delta_{i}_{u}') for u in range(max_h)] for i in
                      range(self.circuits_num)]

            for i in range(self.circuits_num):
                for u in range(max_h):
                    solver.Add(u <= (y[i] + heights[i]) + M * delta[i][u])
                    solver.Add(u >= (y[i] + heights[i]) - M * (1 - delta[i][u]))
                    solver.Add(y[i] <= u + M * delta2[i][u])
                    solver.Add(y[i] >= u - M * (1 - delta2[i][u]))

                    solver.Add(widths[i] - M * delta[i][u] - M * delta2[i][u] <= c_w[i][u] <= widths[i] + M * delta[i][
                        u] + M * delta2[i][u])
                    solver.Add(-M * (1 - delta[i][u]) - M * (1 - delta2[i][u]) <= c_w[i][u] <= widths[i] + M * (
                            1 + delta[i][u]) + M * (1 + delta2[i][u]))

            # for i in range(self.circuits_num):
            #     for u in range(max_h):
            #         solver.Add(0 <= - u + y[i] + M * c_w[i][u] <= M - widths[i])
            #         solver.Add(0 <= u - (y[i] + heights[i]) + M * c_w[i][u] <= M - widths[i])

            for u in range(max_h):
                solver.Add(self.max_width >= sum([c_w[i][u] for i in range(self.circuits_num)]))

                # for u in range(plate_height):
                # self.sol.add(
                #     self.max_width >= Sum([If(And(self.y_positions[i] <= u, u < Sum(self.y_positions[i], self.h[i])),
                #                               self.w[i], 0) for i in range(self.circuits_num)]))

            print('Instantiation time: ', (time.time() - start))
            status = solver.Solve()
            total_time = solver.WallTime() / 1000
            print('Total time elapsed: ', total_time)

            if status == pywraplp.Solver.OPTIMAL:
                circuit_pos = [(w, h, x, y) for (w, h), x, y in
                               zip(self.circuits, [a.solution_value() for a in x], [b.solution_value() for b in y])]

                # self.print_solution(C, X, max_h)
                print([c.solution_value() for c in c_w[2]])
                print([c.solution_value() for c in delta2[2]])
                print([c.solution_value() for c in delta[2]])
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
