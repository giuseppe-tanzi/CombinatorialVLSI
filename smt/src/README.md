# Satisfiability modulo theory
A full description of the ideas and the implementation of this SMT model can be found in this [report](../smt_report.pdf).\
To run the solver you can simply execute the command:<br>
<code>python main.py -s smt</code>

#### Extension

To run the solver with smt-lib you have to execute the command: <br>
<code>python main.py -s smt-lib</code>

To specify the solver to use between Z3 and CVC5, you can add the argument:

- <code>-sol solver, --solsmtlib solver</code> with solver = {z3, cvc5}. Default = z3.

For more instruction on the solver execution, refer to the main [README](../../README.md).

### Results obtained by Z3

![Z3 Results](../out/times_plot.png)
