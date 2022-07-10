import datetime

from minizinc import Model, Solver, Status, Instance

from utils import write_solution


class CPsolver:

    def __init__(self, data, rotation, output_dir, timeout):
        self.data = data
        self.rotation = rotation
        if output_dir == "":
            output_dir = "./cp/out/"
        self.output_dir = output_dir
        self.timeout = timeout
        if rotation:
            self.solver_path = ".\\cp\\src\\model_with_rotations.mzn"
        else:
            self.solver_path = ".\\cp\\src\\model.mzn"

    def solve(self):
        model = Model(self.solver_path)
        or_tools = Solver.lookup("com.google.or-tools")

        solutions = []

        for d in self.data:
            ins_num, plate_width, circuits = d
            instance = Instance(or_tools, model)
            instance["N"] = len(circuits)
            instance["W"] = plate_width

            instance["widths"] = [x for (x, _) in circuits]
            instance["heights"] = [y for (_, y) in circuits]

            result = instance.solve(timeout=datetime.timedelta(seconds=self.timeout), processes=10, random_seed=42)

            if result.status is Status.OPTIMAL_SOLUTION:
                if self.rotation:
                    circuits_pos = [(w, h, x, y) if not r else (h, w, x, y) for (w, h), x, y, r in
                                    zip(circuits, result["coords_x"], result["coords_y"], result["rotation"])]
                else:
                    circuits_pos = [(w, h, x, y) for (w, h), x, y in
                                    zip(circuits, result["coords_x"], result["coords_y"])]
                print(result.statistics['propagations'])
                plate_height = result.objective

                write_solution(self.output_dir, ins_num, ((plate_width, plate_height), circuits_pos),
                               result.statistics['time'] / 1000)

                solutions.append((ins_num, ((plate_width, plate_height), circuits_pos),
                                  result.statistics['time'] / 1000))

        return solutions
