include "globals.mzn";

int: W; % maximum width
int: N; % number of blocks

set of int: BLOCKS = 1..N;

array[BLOCKS, 1..2] of int: shapes;  % matrix containing (w,h) of each block

int: Y = sum([shapes[i,2] | i in BLOCKS]) - min([shapes[i,2] | i in BLOCKS]);
int: X = W - min([shapes[i,1] | i in BLOCKS]);

array[BLOCKS, 1..2] of var 0..Y: coords;  % matrix containing (x,y) of each block 

% for each block, x + w can't be bigger than the maximum width W.
constraint forall(i in BLOCKS)
                 (coords[i,1] + shapes[i,1] <= W);
                 
% Global constraint for no overlapping rectangles.
constraint diffn(
  [coords[i,1] | i in BLOCKS],
  [coords[i,2] | i in BLOCKS],
  [shapes[i,1] | i in BLOCKS],
  [shapes[i,2] | i in BLOCKS]);

% the total height should be as low as possible. 
% var int: H = sum([coords[i,2] + shapes[i,2] | i in BLOCKS]);
var int: H = max([coords[i,2] + shapes[i,2] | i in BLOCKS]);
% var int: H = max([coords[i,2] | i in BLOCKS]);


solve minimize H;

output ["Height : "] ++ [show(H)] ++ [show(coords)];
