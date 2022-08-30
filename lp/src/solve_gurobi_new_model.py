import time
import json
import numpy as np
import gurobipy as gp
from utils import write_solution


class LPsolver:

    def __init__(self, data, rotation, output_dir, timeout):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            output_dir = "./lp/out/no_rot"
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

        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        w, h = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        lower_bound = sum([h[i] * w[i] for i in range(self.circuits_num)]) // self.max_width

        # creating the model
        model = gp.Model()
        model.Params.TimeLimit = self.timeout * 1000
        model.Params.Threads = 4

        max_h = sum(h)

        x = []
        y = []
        widths = []
        heights = []

        # widths_r[i] = widths[i] - rot[i]*widths[i] + rot[i]*heights[i]
        H = model.addVar(vtype='I', lb=lower_bound, ub=max_h, name='h')
        for i in range(self.circuits_num):
            x.append(model.addVar(vtype='I', lb=0, ub=self.max_width - w[i], name=f'x_{i}'))
            y.append(model.addVar(vtype='I', lb=0, ub=max_h - h[i], name=f'y_{i}'))
            widths.append(model.addVar(vtype='I', lb=min(w), ub=max(w), name=f'widths_{i}'))
            heights.append(model.addVar(vtype='I', lb=min(h), ub=max(h), name=f'heights_{i}'))

        if self.rotation:
            rot = []
            for i in range(self.circuits_num):
                rot.append(model.addVar(vtype='I', lb=0, ub=1, name=f'rot_{i}'))
                model.addConstr(widths[i] == w[i] - rot[i] * w[i] + rot[i] * h[i])
                model.addConstr(heights[i] == h[i] - rot[i] * h[i] + rot[i] * w[i])
        else:
            for i in range(self.circuits_num):
                model.addConstr(widths[i] == w[i])
                model.addConstr(heights[i] == h[i])

        # disjunction bool variables
        d = [[[model.addVar(vtype='I', lb=0, ub=1, name=f'd_{i}_{j}_{k}') for k in range(4)] for j in
             range(self.circuits_num)]
            for i in range(self.circuits_num)]
        M = 1000
        for i in range(self.circuits_num):
            model.addConstr(H >= y[i] + h[i])
            # non overlapping constraints
            for j in range(i + 1, self.circuits_num):
                model.addConstr(sum(d[i][j]) >= 1)
                model.addConstr(x[i] + widths[i] <= x[j] + M * (1 - d[i][j][0]))
                model.addConstr(x[j] + widths[j] <= x[i] + M * (1 - d[i][j][1]))
                model.addConstr(y[i] + heights[i] <= y[j] + M * (1 - d[i][j][2]))
                model.addConstr(y[j] + heights[j] <= y[i] + M * (1 - d[i][j][3]))

        model.setObjective(H, gp.GRB.MINIMIZE)
        model.optimize()

        print(model.getJSONSolution())
        solution = json.loads(model.getJSONSolution())
        total_time = solution['SolutionInfo']['Runtime']

        try:
            # print([r.solution_value() for r in rot])
            circuit_pos = [(w, h, x, y) for w, h, x, y in
                           zip([int(a.X) for a in widths], [int(a.X) for a in heights],
                               [int(a.X) for a in x], [int(a.X) for a in y])]

            # self.print_solution(C, X, max_h)
            write_solution(self.output_dir, self.ins_num, ((self.max_width, int(H.X)), circuit_pos), total_time)
            return self.ins_num, ((self.max_width, int(H.X)), circuit_pos), total_time
        except:
            print(f'{self.ins_num})', (None, 0), 0)
            return None, 0


def print_solution(self, C, X, max_h):
    representation = np.zeros((self.max_width, max_h))
    for i in range(self.circuits_num):
        for j in range(len(C[i])):
            if X[i][j].X > 0:
                representation += np.array(C[i][j]).reshape((self.max_width, max_h))
    print("H :", max_h)
    print(representation)
