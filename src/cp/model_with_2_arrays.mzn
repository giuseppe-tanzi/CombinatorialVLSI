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


array[BLOCKS] of var 0..max_X: coords_x;
array[BLOCKS] of var 0..max_Y: coords_y;

% only the right box can't be bigger than the maximum width W.
constraint  max([coords_x[i] + shapes[i,1] | i in BLOCKS]) <= W;
                 
% Global constraint for no overlapping rectangles.
constraint diffn(
  coords_x,
  coords_y,
  [shapes[i,1] | i in BLOCKS],
  [shapes[i,2] | i in BLOCKS]);
  
% breaking symmetries.
include "lex_lesseq.mzn"; 
% MAXIMUM EFFECTIVE WIDTH
var int: W_E = max([coords_x[i] + shapes[i,1] | i in BLOCKS]);

constraint symmetry_breaking_constraint(
  lex_lesseq(coords_y, [H - coords_y[i] - shapes[i,2] | i in BLOCKS])
);

constraint symmetry_breaking_constraint(
  lex_lesseq(coords_x, [W_E - coords_x[i] - shapes[i,1] | i in BLOCKS])
);

% Cumulative constraint
constraint cumulative(coords_y, [shapes[i,2] | i in BLOCKS], [shapes[i,1] | i in BLOCKS], W);

constraint cumulative(coords_x, [shapes[i,1] | i in BLOCKS], [shapes[i,2] | i in BLOCKS], H);

constraint forall(i in BLOCKS) (H >= coords_y[i] + shapes[i,2]);

%solve :: seq_search([
%    int_search(coords_y, first_fail, indomain_min),
%    int_search(coords_x, first_fail, indomain_min)])
%    minimize H;

solve 
  :: int_search([H], input_order, indomain_min)
  minimize H;

output ["Height : "] ++ [show(H)];
output ["\nCoord X: "] ++ [show(coords_x)];
output ["\nCoord Y: "] ++ [show(coords_y)];