include "globals.mzn";
%mzn_ignore_symmetry_breaking_constraints=true

int: W; % maximum width
int: N; % number of circuits
var min_H..max_H: H;

set of int: CIRCUITS = 1..N;

array[CIRCUITS, 1..2] of int: shapes;  % matrix containing (w,h) of each circuit

int: max_X = W - min([shapes[i,1] | i in CIRCUITS]);
int: max_H = sum([shapes[i,2] | i in CIRCUITS]);
int: max_Y = max_H - min([shapes[i,2] | i in CIRCUITS]);
int: min_H = sum([shapes[i,2] * shapes[i,1]| i in CIRCUITS]) div W;


array[CIRCUITS] of var 0..max_X: coords_x;
array[CIRCUITS] of var 0..max_Y: coords_y;

% only the right box can't be bigger than the maximum width W.
constraint  max([coords_x[i] + shapes[i,1] | i in CIRCUITS]) <= W;
                 
% Global constraint for no overlapping circuit.
constraint diffn(
  coords_x,
  coords_y,
  [shapes[i,1] | i in CIRCUITS],
  [shapes[i,2] | i in CIRCUITS]);
  
% breaking symmetries.
include "lex_lesseq.mzn"; 
% MAXIMUM EFFECTIVE WIDTH
var int: W_E = max([coords_x[i] + shapes[i,1] | i in CIRCUITS]);

constraint symmetry_breaking_constraint(
  lex_lesseq(coords_y, [H - coords_y[i] - shapes[i,2] | i in CIRCUITS])
);

constraint symmetry_breaking_constraint(
  lex_lesseq(coords_x, [W_E - coords_x[i] - shapes[i,1] | i in CIRCUITS])
);

% Cumulative constraint
constraint cumulative(coords_y, [shapes[i,2] | i in CIRCUITS], [shapes[i,1] | i in CIRCUITS], W);

constraint cumulative(coords_x, [shapes[i,1] | i in CIRCUITS], [shapes[i,2] | i in CIRCUITS], H);

constraint forall(i in CIRCUITS) (H >= coords_y[i] + shapes[i,2]);

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