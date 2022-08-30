# VLSI Optimization

Authors:

- Enrico Pallotta
- Flavio Pinzarrone
- Giuseppe Tanzi <br>

Project work for the "Combinatorial Decision Making and Optimization" course of the Artificial Intelligence master's
degree at University of Bologna.

Very Large Scale Integration (VLSI) is a very well known problem both in literature and in industry. Also known as 2-D
Strip Packing Problem (2-SPP),
it consists in deciding how to place a given set of rectangular circuits in a fixed-width plate so that no circuit
overlaps with any other, and the height of the plate is minimized.

There are also many variant of this problem, but we considered the one in which each circuit can also be placed after a
rotation of 90°, so basically with width and height exchanged.

In this repository you can find four solution for this problem which use four different approaches:

- Constraint Programming ([CP](./cp))
- [SAT](./sat)
- Satisfiability Modulo Theory ([SMT](./sat))
- Integer Linear Programming ([ILP](.lp))

## Usage

All the solvers can be used by running the file <code>main.py</code> with the command <code>python main.py</code> and
the following arguments:

- <code>-s solver, --solver solver</code> with solver = {cp, sat, smt, smtlib, lp}. Selects the solver to use.
- <code>-t T, --timeout T</code> Set the timeout in T seconds, default = 300s.
- <code>-n N, --num_instance N</code> Select an instance between 1 and 40, default = 0 means solve all.
- <code>-i path, --input_dir path</code> Specify the path from where take the input txt files, default
  = "[./input](./input)"
- <code>-o path, --output_dir path</code> Specify the path in which the results will be generated, default = "
  ./solver/out"
- <code>-r, --rotation</code> Enable resolution with allowed 90° rotations. Disabled by default.
- <code>-v, --visualize</code> Visualize the solution for each instance solved using matplotlib. Disabled by default.
- <code>-p, --plot</code> If enabled, skip the solving process of all given instances and uses the output txt files for
  the given solver to plot a graph of solving times. Disabled by default.

## References

https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0245267
