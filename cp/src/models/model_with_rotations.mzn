include "globals.mzn";
include "lex_lesseq.mzn"; 

int: W; % maximum width
int: N; % number of blocks
var lb..ub: H; % total height to minimize

set of int: CIRCUITS = 1..N;

% input shapes of the circuits.
array[CIRCUITS] of int: w;
array[CIRCUITS] of int: h;

% upper bound for circuits' positions.
int: max_X = W - min(w);
int: max_Y = ub - min(h);

% lower and upper bound for the total height H.
int: lb = sum([w[i] * h[i]| i in CIRCUITS]) div W;
int: ub = sum(h);

array[CIRCUITS] of var bool: rotation;

% actual widths and heights of circuits after a possible rotation of 90 degrees.
array[CIRCUITS] of var int: widths = [if rotation[i] then h[i] else w[i] endif | i in CIRCUITS];
array[CIRCUITS] of var int: heights = [if rotation[i] then w[i] else h[i] endif | i in CIRCUITS];

array[CIRCUITS] of var 0..max_X: x;
array[CIRCUITS] of var 0..max_Y: y;

array[CIRCUITS] of int : ordered_c = sort_by(CIRCUITS, [-w[i] * h[i]| i in CIRCUITS]);

% DOMAIN CONSTRAINT
% The placement of the circuits must consider its actual width (after possible rotation) and the width of the plate.
constraint forall(i in CIRCUITS)(W >= x[i] + widths[i]);

% The total height should be as low as possible.
constraint forall(i in CIRCUITS)(H >= y[i] + heights[i]);
                 
% Global constraint for no overlapping rectangles.
constraint diffn(
  x,
  y,
  widths,
  heights);
  
% Cumulative constraint
constraint cumulative(y, heights, widths, W);
  
% Maximum effective width used later in symmetry breaking.
var int: W_E = max([x[i] + widths[i] | i in CIRCUITS]);

% SYMMETRY BREAKING

% Vertical flip
constraint symmetry_breaking_constraint(
  lex_lesseq(y, [H - y[i] - heights[i] | i in CIRCUITS])
);

% Horizontal flip
constraint symmetry_breaking_constraint(
  lex_lesseq(x, [W_E - x[i] - widths[i] | i in CIRCUITS])
);

% The biggest circuit is always placed under and on the left wrt the second biggest
constraint symmetry_breaking_constraint(
  let {
    int: c1 = ordered_c[1], int: c2 = ordered_c[2]
  } in lex_less([y[c1],x[c1]], [y[c2],x[c2]])
);

% square rotation constraint
constraint symmetry_breaking_constraint(
  forall(i in CIRCUITS)(h[i] == w[i] -> rotation[i]==false)
);

solve 
  :: int_search([H], input_order, indomain_min)
  minimize H;

output ["Height : "] ++ [show(H)];
output ["\nRotation : "] ++ [show(rotation)];
output ["\nCoord X: "] ++ [show(x)];
output ["\nCoord Y: "] ++ [show(y)];