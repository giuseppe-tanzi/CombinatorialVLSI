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

array[CIRCUITS] of int : ordered_c = sort_by(CIRCUITS, [-shapes[i,2]*shapes[i,1] | i in CIRCUITS]);

% only the right box can't be bigger than the maximum width W.
constraint forall(i in CIRCUITS) (W >= coords_x[i] + shapes[i,1])::domain;

constraint forall(i in CIRCUITS) (H >= coords_y[i] + shapes[i,2])::domain;
                 
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

%constraint symmetry_breaking_constraint(
%  lex_lesseq(coords_y, [H - coords_y[i] - shapes[i,2] | i in CIRCUITS])
%);

constraint symmetry_breaking_constraint(
  lex_lesseq(coords_x, [W_E - coords_x[i] - shapes[i,1] | i in CIRCUITS])
);

% The biggest circuit is always placed under and on the left wrt the second biggest
constraint symmetry_breaking_constraint(
  let {
    int: c1 = ordered_c[1], int: c2 = ordered_c[2]
  } in lex_less([coords_y[c1],coords_x[c1]], [coords_y[c2],coords_x[c2]])
);

constraint 
  forall(c in CIRCUITS)(
    member([0] ++ [coords_x[o] + shapes[o, 1] | o in CIRCUITS where o != c], coords_x[c]) /\
    member([0] ++ [coords_y[o] + shapes[o, 2] | o in CIRCUITS where o != c], coords_y[c])
  );

% Cumulative constraint
constraint cumulative(coords_y, [shapes[i,2] | i in CIRCUITS], [shapes[i,1] | i in CIRCUITS], W);

constraint cumulative(coords_x, [shapes[i,1] | i in CIRCUITS], [shapes[i,2] | i in CIRCUITS], H);


%solve :: seq_search([
%    int_search(coords_y, first_fail, indomain_min),
%    int_search(coords_x, first_fail, indomain_min),
%    int_search([H], input_order, indomain_min)])
%    minimize H;

solve 
  :: int_search([H], input_order, indomain_min)
  minimize H;

output ["Height : "] ++ [show(H)];
output ["\nCoord X: "] ++ [show(coords_x)];
output ["\nCoord Y: "] ++ [show(coords_y)];