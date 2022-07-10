import time

from ortools.linear_solver import pywraplp
from utils import write_solution


class LPsolver:

    def __init__(self, data, output_dir, timeout):
        self.data = data
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

    def solve_instance(self, instance):
        start = time.time()
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        w, h = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        lower_bound = sum([h[i] * w[i] for i in range(self.circuits_num)]) // self.max_width

        # creating the model
        solver = pywraplp.Solver.CreateSolver('BOP')
        solver.SetTimeLimit(self.timeout * 1000)
        # solver.EnableOutput()
        solver.SetNumThreads(8)

        x = []
        y = []
        max_h = sum(h)

        # widths_r[i] = widths[i] - rot[i]*widths[i] + rot[i]*heights[i]
        H = solver.IntVar(lb=lower_bound, ub=max_h, name='h')
        for i in range(self.circuits_num):
            x.append(solver.IntVar(lb=0, ub=self.max_width - w[i], name=f'x_{i}'))
            y.append(solver.IntVar(lb=0, ub=max_h - h[i], name=f'y_{i}'))

        # disjunction bool variables
        d = [
            [[solver.IntVar(lb=0, ub=1, name=f'd_{i}_{j}_{k}') for k in range(4)] for j in range(self.circuits_num)]
            for i in range(self.circuits_num)]
        M = 1000
        for i in range(self.circuits_num):
            solver.Add(H >= y[i] + h[i])
            # # domain constraints
            # solver.Add(x[i] + w[i] <= self.max_width)
            # solver.Add(y[i] + h[i] <= max_h)
            # non overlapping constraints
            for j in range(i + 1, self.circuits_num):
                solver.Add(sum(d[i][j]) >= 1)
                solver.Add(x[i] + w[i] <= x[j] + M * (1 - d[i][j][0]))
                solver.Add(x[j] + w[j] <= x[i] + M * (1 - d[i][j][1]))
                solver.Add(y[i] + h[i] <= y[j] + M * (1 - d[i][j][2]))
                solver.Add(y[j] + h[j] <= y[i] + M * (1 - d[i][j][3]))

        # # cumulative constraint over rows
        # c_w = [[solver.IntVar(lb=0, ub=max(w), name=f'cw_{i}_{u}') for u in range(max_h)] for i in
        #        range(self.circuits_num)]
        # delta = [[solver.IntVar(lb=0, ub=1, name=f'delta_{i}_{u}') for u in range(max_h)] for i in
        #          range(self.circuits_num)]
        # delta2 = [[solver.IntVar(lb=0, ub=1, name=f'delta_{i}_{u}') for u in range(max_h)] for i in
        #           range(self.circuits_num)]
        # delta3 = [[solver.IntVar(lb=0, ub=1, name=f'delta_{i}_{u}') for u in range(max_h)] for i in
        #           range(self.circuits_num)]
        #
        # for i in range(self.circuits_num):
        #     for u in range(max_h):
        #         solver.Add(u <= (y[i] + heights[i]) + M * delta[i][u])
        #         solver.Add(u >= (y[i] + heights[i]) - M * (1 - delta[i][u]))
        #         solver.Add(y[i] <= u + M * delta2[i][u])
        #         solver.Add(y[i] >= u - M * (1 - delta2[i][u]))
        #         # delta3 = delta \/ delta2
        #         solver.Add(delta3[i][u] <= delta[i][u] + delta2[i][u])
        #         solver.Add(delta3[i][u] >= delta[i][u])
        #         solver.Add(delta3[i][u] >= delta2[i][u])
        #
        #         # c_w[i][u] = widths[i] if block i occupies a row at height u, otherwise is 0
        #         solver.Add(widths[i] - M * delta3[i][u] <= c_w[i][u])
        #         solver.Add(c_w[i][u] <= widths[i] + M * delta3[i][u])
        #         solver.Add(-M * (1 - delta3[i][u]) <= c_w[i][u])
        #         solver.Add(c_w[i][u] <= M * (1 - delta3[i][u]))
        #
        # for u in range(max_h):
        #     solver.Add(self.max_width >= sum([c_w[i][u] for i in range(self.circuits_num)]))

        # print('Instantiation time: ', (time.time() - start))
        solver.SetHint([H], [lower_bound])
        solver.Minimize(H)
        status = solver.Solve()
        total_time = solver.WallTime() / 1000
        # print('Total time elapsed: ', total_time)

        if status == pywraplp.Solver.OPTIMAL:
            circuit_pos = [(width, height, x, y) for width, height, x, y in
                           zip(w, h, [a.solution_value() for a in x], [a.solution_value() for a in y])]

            # self.print_solution(C, X, max_h)
            write_solution(self.output_dir, self.ins_num, ((self.max_width, H.solution_value()), circuit_pos), total_time)
            return self.ins_num, ((self.max_width, int(H.solution_value())), circuit_pos), total_time
        else:
            write_solution(self.output_dir, self.ins_num, None, 0)
            return self.ins_num, None, 0
