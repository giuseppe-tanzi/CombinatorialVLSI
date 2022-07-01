import subprocess
import time

import numpy as np

file = 'vls1.smt2'

# Number of queens
W = 8
CIRCUITS = 4
shapes = np.array([[3, 3], [3, 5], [5, 3], [5, 5]])

height_low_bound = int(np.sum([shapes[i, 1] * shapes[i, 0] for i in range(CIRCUITS)]) / W)
height_upper_bound = np.sum(shapes[:, 1])

lines = []

# Decision Variables
lines.append("(declare-fun h () Int)")
lines.append("(declare-fun x (Int) Int)")
lines.append("(declare-fun y (Int) Int)")

# Domain
lines += [f"(assert (and (>= (select x {i}) 0) (<= (select x {i}) (- {W} {shapes[i, 0]}))))" for i in range(CIRCUITS)]
lines += [f"(assert (and (>= (select y {i}) 0) (<= (select y {i}) (- {height_upper_bound} {shapes[i, 1]}))))" for i in
          range(CIRCUITS)]
lines += [f"(assert (and (>= h {height_low_bound}) (<= h {height_upper_bound})))"]

# Constraints
lines += [f"(assert (and (>= (select x {i}) 0) (<= (+ (select x {i}) {shapes[i, 0]}) {W})))" for i in range(CIRCUITS)]
lines += [f"(assert (and (>= (select y {i}) 0) (<= (+ (select y {i}) {shapes[i, 1]}) h)))" for i in range(CIRCUITS)]
lines += [f"(assert (or "
          f"(<= (+ (select x {i}) {shapes[i, 0]}) (select x {j})) "
          f"(<= (+ (select x {j}) {shapes[j, 0]}) (select x {i})) "
          f"(<= (+ (select y {i}) {shapes[i, 1]}) (select y {j})) "
          f"(<= (+ (select y {j}) {shapes[j, 1]}) (select y {i}))))" for i in range(CIRCUITS) for j in range(CIRCUITS)
          if i != j]

# Optimization
lines.append("(minimize h)")

# Symmetry Breaking
# TODO


# Result
lines.append("(check-sat)")
lines.append(f"(get-value ({' '.join([f'(select x {i}) (select y {i})' for i in range(CIRCUITS)])}))")
lines.append(f"(get-value (h))")

with open(file, "w") as f:
    for line in lines:
        f.write(line + "\n")

bashCommand = f"z3 -smt2 {file}"

# TODO: SET TIMEOUT
start_time = time.time()
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
time = time.time() - start_time
output, error = process.communicate()

print(output.decode('ascii'))
print(time)
