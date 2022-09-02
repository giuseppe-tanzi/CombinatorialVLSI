include "globals.mzn";
include "lex_lesseq.mzn"; 

int: W; % maximum width
int: N; % number of circuits
var lb..ub: H; % total height to minimize

set of int: CIRCUITS = 1..N;

% input shapes of the circuits.
array[CIRCUITS] of int: w;
array[CIRCUITS] of int: h;

% lower and upper bound for the total height H.
int: lb = sum([w[i] * h[i]| i in CIRCUITS]) div W;
int: ub = sum(h);

% domain upper bound for circuits' positions.
int: max_X = W - min(w);
int: max_Y = ub - min(h);

array[CIRCUITS] of var 0..max_X: x;
array[CIRCUITS] of var 0..max_Y: y;

array[CIRCUITS] of int : ordered_c = sort_by(CIRCUITS, [-w[i] * h[i]| i in CIRCUITS]);

% DOMAIN CONSTRAINT
% Plate bounds constraints (width and height)
constraint forall(i in CIRCUITS) (W >= x[i] + w[i]);

constraint forall(i in CIRCUITS) (H >= y[i] + h[i]);
                 
% Global constraint for no overlapping rectangles.
constraint diffn(
  x,
  y,
  w,
  h);
  
% Cumulative constraints
constraint cumulative(y, h, w, W);

constraint cumulative(x, w, h, H);
  
% Maximum effective width used later in symmetry breaking.
var int: W_E = max([x[i] + w[i] | i in CIRCUITS]);

% SYMMETRY BREAKING

% Horizontal flip
constraint symmetry_breaking_constraint(
  lex_lesseq(x, [W_E - x[i] - w[i] | i in CIRCUITS])
);

% The biggest circuit is always placed under and on the left wrt the second biggest
constraint symmetry_breaking_constraint(
  let {
    int: c1 = ordered_c[1], int: c2 = ordered_c[2]
  } in lex_less([y[c1],x[c1]], [y[c2],x[c2]])
);

solve 
  :: int_search([H], input_order, indomain_min)
  minimize H;

output ["Height : "] ++ [show(H)];
output ["\nCoord X: "] ++ [show(x)];
output ["\nCoord Y: "] ++ [show(y)];