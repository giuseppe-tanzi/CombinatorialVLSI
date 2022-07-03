include "globals.mzn";
%mzn_ignore_symmetry_breaking_constraints=true

int: W; % maximum width
int: N; % number of blocks
var min_H..max_H: H;

set of int: CIRCUITS = 1..N;

array[CIRCUITS] of int: widths;
array[CIRCUITS] of int: heights;

int: max_X = W - min(widths);
int: max_H = sum(heights);
int: max_Y = max_H - min(heights);
int: min_H = sum([widths[i] * heights[i]| i in CIRCUITS]) div W;

array[CIRCUITS] of var bool: rotation;

array[CIRCUITS] of var int: shape_x_r = [if rotation[i] then heights[i] else widths[i] endif | i in CIRCUITS];

array[CIRCUITS] of var int: shape_y_r = [if rotation[i] then widths[i] else heights[i] endif | i in CIRCUITS];

array[CIRCUITS] of var 0..max_X: coords_x;
array[CIRCUITS] of var 0..max_Y: coords_y;

% only the right box can't be bigger than the maximum width W.
constraint  max([coords_x[i] + shape_x_r[i] | i in CIRCUITS]) <= W;
                 
% Global constraint for no overlapping rectangles.
constraint diffn(
  coords_x,
  coords_y,
  shape_x_r,
  shape_y_r);
  
include "lex_lesseq.mzn"; 
% MAXIMUM EFFECTIVE WIDTH
var int: W_E = max([coords_x[i] + shape_x_r[i] | i in CIRCUITS]);

constraint forall(i in CIRCUITS)(heights[i] > W -> rotation[i]==false);

% breaking symmetries.
constraint symmetry_breaking_constraint(
  lex_lesseq(coords_y, [H - coords_y[i] - shape_y_r[i] | i in CIRCUITS])
);

constraint symmetry_breaking_constraint(
  lex_lesseq(coords_x, [W_E - coords_x[i] - shape_x_r[i] | i in CIRCUITS])
);

% square rotation constraint
constraint symmetry_breaking_constraint(
  forall(i in CIRCUITS)(heights[i] == widths[i] -> rotation[i]==false)
);

% Cumulative constraint
constraint cumulative(coords_y, shape_y_r, shape_x_r, W);

% the total height should be as low as possible. 
constraint forall(i in CIRCUITS) (H >= coords_y[i] + heights[i]);

solve 
  :: int_search([H], input_order, indomain_min)
  minimize H;

output ["Height : "] ++ [show(H)];
output ["\nRotation : "] ++ [show(rotation)];
output ["\nCoord X: "] ++ [show(coords_x)];
output ["\nCoord Y: "] ++ [show(coords_y)];