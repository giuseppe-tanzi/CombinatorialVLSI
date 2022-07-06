import argparse

from cp.solve import CPsolver
from lp.solve import LPsolver
from sat.solve import SATsolver
from src.smt.solve import SMTsolver
from src.smt.solveOMT import OMTsolver
from utils.utils import load_data, display_solution


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--solver", help="Select a solver between cp, sat, smt and lp", default="cp", type=str)
    parser.add_argument("-n", "--num_instance",
                        help="Select the number of the instance you want to solve, default = 0 solve all",
                        default=0, type=int)
    parser.add_argument("-i", "--input_dir",
                        help="Directory where the instance txt files can be found",
                        default="..\\data\\instances_txt\\", type=str)
    parser.add_argument("-o", "--output_dir",
                        help="Directory where the output will be saved", default="")
    parser.add_argument("-r", "--rotation", help="Flag to decide whether it is possible use rotated circuits",
                        default=False, type=bool)
    parser.add_argument("-v", "--visualize", help="Enable solution visualization", default=False, type=bool)
    parser.add_argument("-t", "--timeout", help="Timeout in seconds", default=300)
    parser.add_argument("-p", "--report", help="Make the report", default=False)
    args = parser.parse_args()
    print(args)

    print("Loading instances")
    data = load_data(args.num_instance, args.input_dir)
    print(data)
    if args.solver == "cp":
        solver = CPsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=args.timeout)
    elif args.solver == "sat":
        solver = SATsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=args.timeout)
    elif args.solver == "smt":
        solver = SMTsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=args.timeout)
    elif args.solver == "omt":
        solver = OMTsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=args.timeout)
    elif args.solver == "lp":
        solver = LPsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=args.timeout)
    else:
        raise argparse.ArgumentError("Please select a solver between cp, sat, smt and lp.")

    print("Solving with", args.solver)
    solutions = solver.solve()

    if args.visualize:
        for sol in solutions:
            circuits = [(w, h) for (w, h, _, _) in sol[1][1]]
            circuits_pos = [(x, y) for (_, _, x, y) in sol[1][1]]
            display_solution(f'ins-{sol[0]}', (sol[1][0][0], sol[1][0][1]), len(sol[1][1]), circuits, circuits_pos)
    if args.report:
        # TODO : create the report
        pass


if __name__ == '__main__':
    main()
