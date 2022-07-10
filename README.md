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
rotation of 90 degrees, so basically with width and height exchanged.

In this repository you can find four solution for this problem which use four different approaches:
- Constraint Programming (CP)
- SAT
- Satisfiability Modulo Theory (SMT)
- Integer Linear Programming (ILP)

## Citazioni

https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0245267
