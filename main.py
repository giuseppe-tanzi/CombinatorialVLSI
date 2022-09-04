import argparse

from cp.src.solve import CPsolver
from lp.src.solve import LPsolver
from lp.src.solve_rotation import LPsolverRot
from sat.src.solve import SATsolver
from smt.src.solve import SMTsolver
from smt.src.solve_rotation import SMTsolverRot
from smt.src.solve_smtlib import SMTLIBsolver
from smt.src.solve_smtlib_rotation import SMTLIBsolverRot
from utils import load_data, display_solution, plot_times


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--solver", help="Select a solver between cp, sat, smt and lp", default="cp", type=str)
    parser.add_argument("-n", "--num_instance",
                        help="Select the number of the instance you want to solve, default = 0 solve all",
                        default=0, type=int)
    parser.add_argument("-i", "--input_dir",
                        help="Directory where the instance txt files can be found",
                        default="./input", type=str)
    parser.add_argument("-o", "--output_dir",
                        help="Directory where the output will be saved", default="")
    parser.add_argument("-r", "--rotation", help="Flag to decide whether it is possible use rotated circuits",
                        default=False, action='store_true')
    parser.add_argument("-v", "--visualize", help="Enable solution visualization", default=False, action='store_true')
    parser.add_argument("-t", "--timeout", help="Timeout in seconds", default=300)
    parser.add_argument("-p", "--plot", help="Plot of solving times", default=False, action='store_true')
    parser.add_argument("-sol", "--solsmtlib", help="Solver used for SMTLib", default="z3", type=str)
    args = parser.parse_args()
    print(args)

    print("Loading instances")
    if args.plot:
        data = []
    else:
        data = load_data(args.num_instance, args.input_dir)
    print(data)
    if args.solver == "cp":
        solver = CPsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=int(args.timeout))
    elif args.solver == "sat":
        solver = SATsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=int(args.timeout))
    elif args.solver == "smt":
        if args.rotation:
            solver = SMTsolverRot(data=data, output_dir=args.output_dir, timeout=int(args.timeout))
        else:
            solver = SMTsolver(data=data, output_dir=args.output_dir, timeout=int(args.timeout))
    elif args.solver == "smtlib":
        if args.solsmtlib != 'z3' and args.solsmtlib != 'cvc5':
            raise argparse.ArgumentError(None, "Please select a smtlib solver between z3 and cvc5.")
        if args.rotation:
            solver = SMTLIBsolverRot(data=data, output_dir=args.output_dir, timeout=int(args.timeout),
                                     solver=args.solsmtlib)
        else:
            solver = SMTLIBsolver(data=data, output_dir=args.output_dir, timeout=int(args.timeout),
                                  solver=args.solsmtlib)
    elif args.solver == "lp":
        if args.rotation:
            solver = LPsolverRot(data=data, output_dir=args.output_dir, timeout=int(args.timeout))
        else:
            solver = LPsolver(data=data, output_dir=args.output_dir, timeout=int(args.timeout))
    else:
        raise argparse.ArgumentError(None, "Please select a solver between cp, sat, smt and lp.")

    print("Solving with", args.solver, "rotation", args.rotation)
    solutions = solver.solve()

    if args.visualize:
        for sol in solutions:
            if sol[1] != None:
                circuits = [(w, h) for (w, h, _, _) in sol[1][1]]
                circuits_pos = [(x, y) for (_, _, x, y) in sol[1][1]]
                display_solution(f'ins-{sol[0]}', (sol[1][0][0], sol[1][0][1]), len(sol[1][1]), circuits, circuits_pos)
    if args.plot:
        plot_times(solver.output_dir)


if __name__ == '__main__':
    main()
