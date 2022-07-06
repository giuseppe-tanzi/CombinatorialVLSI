include "globals.mzn";
include "lex_lesseq.mzn"; 

int: W; % maximum width
int: N; % number of circuits
var min_H..max_H: H;

set of int: CIRCUITS = 1..N;

array[CIRCUITS] of int: widths;  % matrix containing (w,h) of each circuit
array[CIRCUITS] of int: heights;

int: max_X = W - min(widths);
int: max_H = sum(heights);
int: max_Y = max_H - min(heights);
int: min_H = sum([widths[i] * heights[i]| i in CIRCUITS]) div W;


array[CIRCUITS] of var 0..max_X: coords_x;
array[CIRCUITS] of var 0..max_Y: coords_y;

array[CIRCUITS] of int : ordered_c = sort_by(CIRCUITS, [-widths[i] * heights[i]| i in CIRCUITS]);

% Plate bounds constraints (width and height)
constraint forall(i in CIRCUITS) (W >= coords_x[i] + widths[i]);

constraint forall(i in CIRCUITS) (H >= coords_y[i] + heights[i]);
                 
% No-overlapping constraint
constraint diffn(
  coords_x,
  coords_y,
  widths,
  heights);
  
% Cumulative constraints
constraint cumulative(coords_y, heights, widths, W);

constraint cumulative(coords_x, widths, heights, H);
  
% Maximum effective width
var int: W_E = max([coords_x[i] + widths[i] | i in CIRCUITS]);

% Breaking symmetries

%constraint symmetry_breaking_constraint(
%  lex_lesseq(coords_y, [H - coords_y[i] - heights[i] | i in CIRCUITS])
%);

constraint symmetry_breaking_constraint(
  lex_lesseq(coords_x, [W_E - coords_x[i] - widths[i] | i in CIRCUITS])
);

% The biggest circuit is always placed under and on the left wrt the second biggest
constraint symmetry_breaking_constraint(
  let {
    int: c1 = ordered_c[1], int: c2 = ordered_c[2]
  } in lex_less([coords_y[c1],coords_x[c1]], [coords_y[c2],coords_x[c2]])
);

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