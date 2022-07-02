from utils.utils import write_solution
import gurobipy as gp
import time
import numpy as np


class LPsolver:

    def __init__(self, data, rotation, output_dir, timeout):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            output_dir = "../data/output_lp/"
        self.output_dir = output_dir
        self.timeout = timeout

    def solve(self):
        for d in self.data:
            solution = self.solve_instance(d)
            ins_num = d[0]
            # write_solution(ins_num, solution[0], solution[1])

    def solve_instance(self, instance):
        _, self.max_width, self.circuits = instance
        self.circuits_num = len(self.circuits)

        widths, heights = ([i for i, _ in self.circuits], [j for _, j in self.circuits])

        lower_bound = sum([heights[i] * widths[i] for i in range(self.circuits_num)]) // self.max_width
        upper_bound = sum(heights) - min(heights)

        def valid_positions(c_w, c_h, max_width, max_h):
            val_pos = []
            for i in range(max_width):
                for j in range(max_h):
                    if i + c_w <= max_width and j + c_h <= max_h:
                        create_binary_encoding = np.zeros(max_h * max_width)
                        for k in range(j, j + c_h):
                            create_binary_encoding[k * max_width + i: k * max_width + i + c_w] = 1
                        val_pos.append(create_binary_encoding)
            return val_pos

        for max_h in range(lower_bound - 1, upper_bound + 1):

            # creating the tensor which contains, for each circuit, all its possible valid positions
            C = [valid_positions(widths[i], heights[i], self.max_width, max_h) for i in range(self.circuits_num)]

            # creating the model
            model = gp.Model()

            # X contiene, per ogni circuito, un numero di liste pari al numero di posizioni valide che il circuito
            # può ricoprire nella plate di dimensioni max_width * current_h (lower_bound)
            X = []
            for i in range(self.circuits_num):
                X.append([model.addVar(vtype='I', name=f'x_{i}_{j}', lb=0, ub=1) for j in range(len(C[i]))])

            # no overlapping
            # ogni posizione p sulla plate non deve essere occupata da più di 1 circuito
            for p in range(np.array(C[0]).shape[1]):
                model.addConstr(
                    sum([C[i][j][p] * X[i][j] for i in range(self.circuits_num) for j in range(len(C[i]))]) <= 1)

            # ogni circuito deve essere piazzato esattamente una volta
            for i in range(self.circuits_num):
                model.addConstr(sum([X[i][j] for j in range(len(C[i]))]) == 1)

            model.optimize()

            try:
                self.print_solution(C, X, max_h)
                break
            except:
                pass

    def print_solution(self, C, X, max_h):
        # this first line is used only to make the print fail early in case there's no solution for the current h.
        X[0][0].X
        representation = np.zeros((self.max_width, max_h))
        for i in range(self.circuits_num):
            for j in range(len(C[i])):
                if X[i][j].X > 0:
                    representation += np.array(C[i][j]).reshape((self.max_width, max_h))
        print("H :", max_h)
        print(representation)
