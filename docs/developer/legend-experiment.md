# Free-space legend design

The local `dev` experiment proposes legend positions between the standard named locations. It does not change the default policy. See [experiment usage](../../tools/experiments/README.md) for the comparison script and temporary finishing context.

## Spatial cost

Measure the legend width $w$ and height $h$ with Matplotlib. Divide the axes interior, after border padding, into an $N\times N$ grid; the prototype uses $N=128$. If the interior width and height are $A$ and $B$, the window dimensions are

$$
m=\left\lceil\frac{Nw}{A}\right\rceil,\qquad
n=\left\lceil\frac{Nh}{B}\right\rceil.
$$

For candidate origin $(c,r)$, let $W_{c,r}$ contain its $m\times n$ cells. Every finite visible scatter centre contributes one count to its cell, producing integer grid $G$. Let $H_\ell$ mark cells traversed by visible line $\ell$, and $Q$ mark the union of visible text bounding boxes. The costs are

$$
T(c,r)=\sum_{(i,j)\in W_{c,r}}Q(i,j),
$$

$$
D(c,r)=\sum_{(i,j)\in W_{c,r}}G(i,j)
+10\sum_\ell\mathbf{1}\!\left[\sum_{(i,j)\in W_{c,r}}H_\ell(i,j)>0\right].
$$

The line weight matches the existing scorer's ratio of 0.1 per intersecting line to 0.01 per covered scatter centre. Text cost has higher priority than data cost. Points are aggregated without subsampling; short line segments are traced at grid-cell spacing. This placement grid does not rasterise the exported plot.

## Window evaluation

For a grid $G$, construct a padded summed-area table

$$
S(a,b)=\sum_{i<a,\,j<b}G(i,j).
$$

Each window sum then requires four table entries:

$$
\sum_{W_{c,r}}G
=S(r+n,c+m)-S(r,c+m)-S(r+n,c)+S(r,c).
$$

NumPy evaluates the complete cost map in bulk. Scatter aggregation takes linear work in the number of points; each rectangular query has constant cost after preprocessing. The grid still searches candidate origins. It does not remove optimisation or prove a continuous global optimum.

## Deterministic ties

First retain origins with minimum $T$, then minimum $D$. If this minimum-cost set touches the grid boundary, prefer alignment with axes edges and corners. Otherwise, repeated eight-neighbour erosion measures clearance inside the minimum-cost origin region; prefer its interior.

With $C=N-m$ and $R=N-n$, the alignment penalty is

$$
E(c,r)=\min(c,C-c)+\min(r,R-r).
$$

The final lexicographic key is $(T,D,-K,E,-r,-c)$, where $K$ is erosion depth, or zero when the minimum-cost set touches the boundary. The last terms prefer the upper-right side when previous terms tie. Clearance concerns feasible legend origins, not exact distance to rendered marker outlines.

## Limits and integration

The prototype supports ordinary axes, scatter and short line paths. Complex artists, long paths and windows that do not fit use the existing selector. Quantisation, text-box unions and marker footprints make the grid a proxy for exact visual overlap; subjective presentation quality requires inspection.

The experimental hybrid first evaluates conventional locations in their existing order and stops on a zero clipping/text/data score. Otherwise it audits the grid proposal using the same exact scorer as the classic policy. Ties retain the conventional location, with relative tolerance $10^{-10}$ and absolute tolerance $10^{-12}$ for floating-point comparisons.

For a data-only improvement, acceptance also requires

$$
\frac{D_{classic}-D_{proposal}}{D_{classic}}\ge\delta,
\qquad \delta=0.10.
$$

This threshold is a conservative presentation preference, not a mathematical constant. Clipping and text retain their higher lexicographic priority. Sensitivity checks compare $\delta=0$, $0.10$ and $0.25$.

Changing placement policy on an already finished figure re-evaluates legend placement without recalculating axes geometry. The experimental context restores the normal policy on exit; subsequent finishing revisits placement as needed. The hybrid remains local to `dev` and is not enabled by default.
