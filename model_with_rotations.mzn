include "globals.mzn";
%mzn_ignore_symmetry_breaking_constraints=true

int: W; % maximum width
int: N; % number of blocks
var min_H..max_H: H;

set of int: BLOCKS = 1..N;

array[BLOCKS, 1..2] of int: shapes;  % matrix containing (w,h) of each block

int: max_X = W - min([shapes[i,1] | i in BLOCKS]);
int: max_H = sum([shapes[i,2] | i in BLOCKS]);
int: max_Y = max_H - min([shapes[i,2] | i in BLOCKS]);
int: min_H = sum([shapes[i,2] * shapes[i,1]| i in BLOCKS]) div W;

array[BLOCKS] of var bool: rotation;

array[BLOCKS] of var int: shape_x_r = [if rotation[i] then shapes[i,2] else shapes[i,1] endif | i in BLOCKS];

array[BLOCKS] of var int: shape_y_r = [if rotation[i] then shapes[i,1] else shapes[i,2] endif | i in BLOCKS];

array[BLOCKS] of var 0..max_X: coords_x;
array[BLOCKS] of var 0..max_Y: coords_y;

% only the right box can't be bigger than the maximum width W.
constraint  max([coords_x[i] + shape_x_r[i] | i in BLOCKS]) <= W;
                 
% Global constraint for no overlapping rectangles.
constraint diffn(
  coords_x,
  coords_y,
  shape_x_r,
  shape_y_r);
  
include "lex_lesseq.mzn"; 
% MAXIMUM EFFECTIVE WIDTH
var int: W_E = max([coords_x[i] + shape_x_r[i] | i in BLOCKS]);

constraint forall(i in BLOCKS)(shapes[i,2] > W -> rotation[i]==false);

% breaking symmetries.
constraint symmetry_breaking_constraint(
  lex_lesseq(coords_y, [H - coords_y[i] - shape_y_r[i] | i in BLOCKS])
);

constraint symmetry_breaking_constraint(
  lex_lesseq(coords_x, [W_E - coords_x[i] - shape_x_r[i] | i in BLOCKS])
);

% square rotation constraint
constraint symmetry_breaking_constraint(
  forall(i in BLOCKS)(shapes[i,2] == shapes[i,1] -> rotation[i]==false)
);

% Cumulative constraint
constraint cumulative(coords_y, shape_y_r, shape_x_r, W);

% the total height should be as low as possible. 
constraint forall(i in BLOCKS) (H >= coords_y[i] + shapes[i,2]);

solve 
  :: int_search([H], input_order, indomain_min)
  minimize H;

output ["Height : "] ++ [show(H)];
output ["\nRotation : "] ++ [show(rotation)];
output ["\nCoord X: "] ++ [show(coords_x)];
output ["\nCoord Y: "] ++ [show(coords_y)];