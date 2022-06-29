import argparse
from time import time
import subprocess
import os


def solve_instance(model, in_file, out_dir, solver="Chuffed"):
    # command to run the model
    command = f'minizinc --solver {solver} -p 1 -t 300000 {model} {in_file} --solver-statistics'

    instance_name = in_file.split('\\')[-1] if os.name == 'nt' else in_file.split('/')[-1]
    instance_name = instance_name[:len(instance_name) - 4]
    out_file = os.path.join(out_dir, instance_name + '-out.txt')
    print(out_file)
    with open(out_file, 'w') as f:
        print(f'{out_file}:', end='\n', flush=True)
        start_time = time()
        print(command)
        subprocess.run(command.split())
        elapsed_time = time() - start_time
        print(f'{elapsed_time * 1000:.1f} ms')
        if (elapsed_time * 1000) < 300000:
            subprocess.run(command.split(), stdout=f)
            f.write('{}'.format(elapsed_time))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--instance", help="Number of the instance to solve", default=2,
                        required=False, type=int)
    args = parser.parse_args()

    model = "model_with_2_arrays.mzn"
    in_file = ".\instances_dzn\ins-" + str(args.instance) + ".dzn"
    out_dir = "out/final"

    solve_instance(model, in_file, out_dir)


if __name__ == '__main__':
    main()
