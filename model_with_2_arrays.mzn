include "globals.mzn";

int: W; % maximum width
int: N; % number of blocks

set of int: BLOCKS = 1..N;

array[BLOCKS, 1..2] of int: shapes;  % matrix containing (w,h) of each block

int: Y = sum([shapes[i,2] | i in BLOCKS]) - min([shapes[i,2] | i in BLOCKS]);
int: X = W - min([shapes[i,1] | i in BLOCKS]);

array[BLOCKS] of var 0..X: coords_x;
array[BLOCKS] of var 0..Y: coords_y;

% only the right box can't be bigger than the maximum width W.
constraint  max([coords_x[i] + shapes[i,1] | i in BLOCKS]) <= W;
                 
% Global constraint for no overlapping rectangles.
constraint diffn(
  [coords_x[i] | i in BLOCKS],
  [coords_y[i] | i in BLOCKS],
  [shapes[i,1] | i in BLOCKS],
  [shapes[i,2] | i in BLOCKS]);
  
% breaking symmetries.
include "lex_lesseq.mzn";
% MAXIMUM EFFECTIVE WIDTH
var int: W_E = max([coords_x[i] + shapes[i,1] | i in BLOCKS]);

constraint
    lex_lesseq([coords_x[i] | i in BLOCKS],
     [((W_E - (W_E div 2)) + ((W_E div 2) - coords_x[i]) - shapes[i,1]) | i in BLOCKS])
;

% Cumulative constraint
constraint cumulative([coords_y[i] | i in BLOCKS], [shapes[i,2] | i in BLOCKS], [shapes[i,1] | i in BLOCKS], W);

% the total height should be as low as possible. 
var int: H = max([coords_y[i] + shapes[i,2] | i in BLOCKS]);

solve minimize H;

output ["Height : "] ++ [show(H)];
output ["\nCoord X: "] ++ [show(coords_x)];
output ["\nCoord Y: "] ++ [show(coords_y)];