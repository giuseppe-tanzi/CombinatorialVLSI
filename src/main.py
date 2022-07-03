import argparse

from cp.solve import CPsolver
from sat.solve import SATsolver
from lp.solve import LPsolver
from utils.utils import load_data


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-s", "--solver", help="Select a solver between cp, sat, smt and lp", default="cp", type=str)
    parser.add_argument("-n", "--num_instances",
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
    args = parser.parse_args()
    print(args)

    print("Loading instances")
    data = load_data(args.num_instances, args.input_dir)
    print(data)
    if args.solver == "cp":
        solver = CPsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=args.timeout)
    elif args.solver == "sat":
        solver = SATsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=args.timeout)
    elif args.solver == "smt":
        pass
        # solver = SMTsolver(num_instance = args.num_instances, rotation = args.rotation, input_dir = args.input_dir, output_dir = args.output_dir, timeout = args.timeout)
    elif args.solver == "lp":
        solver = LPsolver(data=data, rotation=args.rotation, output_dir=args.output_dir, timeout=args.timeout)
    else:
        raise argparse.ArgumentError("Please select a solver between cp, sat, smt and lp.")

    print("Solving with", args.solver)
    solutions = solver.solve()

    if args.visualize:
        # TODO : visualization
        pass

    if args.report:
        # TODO : create the report
        pass


if __name__ == '__main__':
    main()
