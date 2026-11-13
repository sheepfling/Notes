# Two-liquid exploration: specification and proofs

> Type: reference
> Status: needs-review
> Updated: 2026-11-13
> Tags: mathematics, optimization, proofs

Version 0.3. All claims below are conditional on the stated mathematical model. The worked quantities are illustrative, not supplied by the user.

## 1. Scope and well-posedness

A and B are homogeneous, perfectly miscible ingredients. Amounts use one consistent unit. Volumes are additive; no evaporation, reaction, spillage, residual cup film, incomplete stirring, or return of sampled liquid is modeled. Each withdrawal is taken after complete mixing. Supplies are upper bounds; unused supply is allowed.

A sample has fraction x of A, so composition space is [0,1]. The full interval is the exploration domain even if available equipment makes parts unreachable: otherwise a restrictive machine could appear successful merely by redefining the target. An alternate target interval must be stated explicitly.

An actual taste has volume at least m>0. This makes the number of consumed samples finite. Minimum distinguishable separation delta>0 is a different restriction. An arbitrary number of distinct real ratios is possible without a positive separation threshold, but with m>0 finite supplies still bound the number of actual tastes.

Keep three objectives separate:

1. Fixed-N coverage: minimize the largest distance from any target recipe to a tasted recipe.
2. Packing: maximize the number of samples separated by at least delta.
3. Economy: meet a target coverage with fewer tastes, less discard, or less material.

Neither maximizing range nor maximizing variance substitutes for coverage. Pure endpoints alone maximize range but leave all middle mixtures unexplored. Duplicate tastes are legal under coverage-only optimization and must not be reported as new flavors. Tests do not demonstrate sensory distinguishability.

## 2. Canonical state, event order, and accounting

Immediately before taste i, the cup contains q_i=(a_i,b_i), volume V_i=a_i+b_i>0, composition x_i=a_i/V_i, and remaining supply h_i=(A_i,B_i). The initial fill is explicitly charged to supplies: q_1=(u_0,v_0), h_1=(A_0-u_0,B_0-v_0).

Taste s_i>=m; optionally discard d_i>=0; total withdrawal r_i=s_i+d_i<=V_i. These withdrawals have the same composition. Between tastes i and i+1, add u_i>=0 of A and v_i>=0 of B:

    q_(i+1) = (1-r_i/V_i) q_i + (u_i,v_i)
    h_(i+1) = h_i - (u_i,v_i)
    0 < a_(i+1)+b_(i+1) <= C
    h_(i+1) >= (0,0).

An empty intermediate cup is permitted when the action rules allow it. The zero state has no composition. The final taste is also consumed; there is no gratuitous refill after the final taste. Final residual is q_end=(1-r_N/V_N)q_N.

Component-wise accounting for the complete experiment is

    supplied-to-cup = tasted + discarded + final-residual.

Equivalently, starting inventory equals unused source inventory plus these three terms. Never conflate final residual with discard: it remains liquid in the cup unless explicitly discarded. Supply bounds include the initial fill, not just top-ups.

The action set encodes equipment rules: fixed or bounded sample size, discrete source volumes, pure-only refills, mandatory top-off, minimum retained heel, permitted resets, and maximum number of operations. A fixed sip is not automatically optimal among all sips >=m; increasing a withdrawal can improve reachability at a material cost.

## 3. Coverage, separation, and chronological order

For a nonempty multiset X of tasted compositions,

    R(X) = max_{t in [0,1]} min_{x in X} |t-x|.

If y_1<=...<=y_N sorts X, then

    R(X) = max(y_1, 1-y_N, (y_(j+1)-y_j)/2 for j=1,...,N-1).

Proof: on each interior gap the nearest endpoint is farthest at its midpoint; outside the extreme samples the farthest points are domain endpoints. This proves the formula without sampling a plotting grid.

Separation for N>=2 is min_j(y_(j+1)-y_j). Chronological x_i and sorted y_j are different objects. Sorting the physical action sequence is not generally a valid transformation: it changes the intermediate state and consumption. The exact finite search keeps the complete observed history; it does not merge histories merely because they share a current cup and inventory.

A general optimization is therefore: choose an admissible N-taste trajectory minimizing R, with optional separation and endpoint constraints. For variable N, solve each feasible horizon or use a separately declared count/coverage objective. A single arbitrary weighted sum is not assumed.

## 4. Fresh samples: linear programming and a sharper exact solution

Assume the cup may be emptied after every taste, each independent sample can be measured arbitrarily, and C>=m. It is without loss to use exactly m per sample: shrinking a larger independent sample preserves its composition and only reduces resource use. This argument does NOT apply to a carryover trajectory.

For N fixed, the sorted coverage LP is:

    minimize R
    0 <= y_1 <= ... <= y_N <= 1
    y_1 <= R, 1-y_N <= R
    y_(i+1)-y_i <= 2R
    m sum y_i <= A_0
    m (N-sum y_i) <= B_0.

Optional constraints are y_(i+1)-y_i>=delta and/or y_1=0,y_N=1. Both endpoints require N>=2. This is the implementation in solve_fresh.

### Theorem 1: universal coverage bound

Every one of N points covers at most 2R length, so 1<=2NR. Thus R>=1/(2N). The midpoint grid y_i=(2i-1)/(2N) achieves equality. It requires Nm/2 of each source.

With mandatory endpoints, N-1 interior gaps sum to 1. Their largest is at least 1/(N-1), giving R>=1/[2(N-1)]. The endpoint-inclusive uniform grid attains it and again uses Nm/2 of each source.

### Theorem 2: exact optimum with arbitrary ingredient budgets

Let a=A_0/m, b=B_0/m, q=min(a,b). Assume a+b>=N, otherwise even N samples cannot be consumed. Without mandatory endpoints or a positive separation constraint,

    R* = max(1/(2N), max_{1<=k<=N} (k-q)/k^2).

This is a closed-form, finite maximum. For rational quantities it is an exact rational answer, not a floating-point optimization result.

Proof. For a proposed radius R>=1/(2N), the smallest feasible sorted coordinate at each position is

    l_i = max(0, 1-[2(N-i)+1]R),   i=1,...,N.

The last point must be at least 1-R and each preceding gap at most 2R. These bounds are simultaneously attained by l. Its left endpoint obeys l_1<=R because R>=1/(2N). Hence the smallest possible sum is

    L_N(R) = sum_{k=0}^{N-1} max(0,1-(2k+1)R)
           = max_{0<=k<=N} (k-k^2 R).

The last equality holds because the summands before clipping are decreasing: the positive prefix has the greatest prefix sum. Reflection gives the largest feasible sum N-L_N(R). Convex combinations of the minimizing vector and its reflected maximizing vector satisfy all sorted coverage inequalities and realize EVERY sum in this interval.

Budget feasibility requires sum y_i in [N-b,a]. This interval intersects [L_N(R),N-L_N(R)] iff a+b>=N and both a,b>=L_N(R). Therefore q>=k-k^2R for every k=1,...,N. Solving these inequalities for R gives the stated formula. The constructive convex combination proves attainment, not merely a lower bound.

The exact implementation chooses a feasible sum as close to N/2 as possible, then constructs that convex combination. Other optimal configurations can exist.

### Theorem 3: exact budget formula with mandatory pure endpoints

Now N>=2 and each source must satisfy A_0>=m and B_0>=m. Also Nm<=A_0+B_0. Write q=min(A_0,B_0)/m. Then

    R* = max(1/[2(N-1)],
             max_{1<=k<=N-2} (k+1-q)/[k(k+1)]).

For N=2, the second maximum is absent and R*=1/2. Derivation: force y_1=0,y_N=1; the smallest possible sum at radius R is

    L_end(R) = 1 + max_{0<=k<=N-2} (k-k(k+1)R).

Backward gap constraints give y_i=max(0,1-2(N-i)R) for 2<=i<=N. Reflection and convex interpolation supply the same sufficiency argument as Theorem 2.

### Theorem 4: maximum number of distinguishable fresh samples

For delta>0, no mandatory endpoints, and N>=1, feasibility is equivalent to

    (N-1)delta <= 1
    Nm <= A_0+B_0
    m delta N(N-1)/2 <= min(A_0,B_0).

Necessity: sorted ratios satisfy y_i>=(i-1)delta and 1-y_i>=(N-i)delta. Summing yields both ingredient bounds; total volume and interval packing yield the other two inequalities.

Sufficiency: evenly separated grids y_i=t+(i-1)delta, with 0<=t<=1-(N-1)delta, realize every sum in [L,N-L], L=delta N(N-1)/2. The four inequalities ensure this interval intersects [N-B_0/m,A_0/m]. All larger N become harder, so monotone binary search obtains the exact maximum feasible count.

### Theorem 5: fresh preparation is a lower bound for any consuming trajectory

Any N-taste trajectory with samples s_i>=m consumes at least m sum x_i of A and m sum(1-x_i) of B. Neither component can exceed its initial supply. Therefore the same N compositions, sorted and prepared independently at volume m, satisfy the fresh-sample constraints. It follows that

    R*_fresh <= R*_sequential

for the same supplies, minimum sample, and compatible endpoint/separation requirements. This is a relaxation: the fresh model may drop a fixed-first-recipe restriction or mandatory full cup and therefore need not be operationally comparable. If a sequential feasible plan attains this bound, it is globally optimal even among more permissive sequential controls under those same common assumptions.

## 5. Full-cup dynamics, reachability, and impossibility

At each taste the cup has volume C. Withdraw r_i, then refill exactly r_i with A fraction z_i. Thus

    x_(i+1) = (1-r_i/C)x_i + (r_i/C)z_i,
    A addition = r_i z_i, B addition = r_i(1-z_i).

This weighted average proves that a withdrawal alone does not alter composition.

For a fixed replacement fraction f=r/C and arbitrary mixed refill, the next composition lies in [(1-f)x,(1-f)x+f]. Supplies tighten the refill range to

    max(0,1-B_remaining/r) <= z <= min(1,A_remaining/r).

A nonempty feasible z interval is required. The target t>x is reachable with the smallest withdrawal by using pure A:

    r_min = C(t-x)/(1-x).

For t<x use pure B and r_min=C(x-t)/x. These expressions apply when the denominators are nonzero and the requested direction is possible. If t=x, a mixed refill of composition x preserves it; a nonzero pure refill generally does not. Actual withdrawals must also meet sampling/equipment constraints.

If every withdrawal is strictly less than C, any positive amount of a component remains positive after withdrawal. Adding cannot cancel it. Hence a finite partial-refill trajectory cannot visit both pure endpoints. To eliminate an unwanted component exactly requires complete emptying (or a different physical operation not in this model).

For fixed f and repeated pure-A refills, x_k=1-(1-x_0)(1-f)^k. Equal sips produce geometric, not uniformly spaced, concentrations.

### Full-cup material bound

With fixed sip s and N tastes, no discards, and no final refill,

    input total = C+(N-1)s
    tasted total = Ns
    final residual = C-s.

Thus N<=1+floor((A_0+B_0-C)/s), provided the initial fill is possible. Ingredient-specific restrictions may reduce it. For variable s_i>=m, C+(N-1)m is only a lower bound on total input.

## 6. A globally optimizable sequential slice: fixed sip

With s fixed, f=s/C is fixed and the dynamics are affine in x and z. This corrects an overly broad claim that all sequential cases require nonlinear optimization. For a known ordering of visited compositions, the continuous-refill problem is an LP. With unknown order it admits a finite mixed-integer linear formulation.

Variables:

- Chronological x_i in [0,1], i=1,...,N.
- Refill z_i in [0,1], i=1,...,N-1 (continuous, binary, or quantized).
- Sorted y_j in [0,1].
- Assignment P_ij in {0,1}, with each row and column summing to 1.
- Radius R in [0,1].

Impose dynamics, optional fixed x_1, coverage inequalities on y, and budgets:

    C x_1+s sum z_i <= A_0
    C(1-x_1)+s sum(1-z_i) <= B_0.

Match chronological and sorted values with tight M=1 constraints:

    y_j-x_i <= 1-P_ij
    x_i-y_j <= 1-P_ij.

When P_ij=1 equality is enforced; otherwise the inequalities are redundant because both variables are in [0,1]. Every trajectory admits a sorting permutation; every feasible assignment links y to exactly the same multiset. Thus this reformulation is exact, including nonmonotone sequences and ties.

For a refill grid z_i=h_i/K, require integer 0<=h_i<=K. K=1 gives pure sources. This quantizes refills, not the initial mixture. If source volumes must be multiples of q and s=Kq, this grid implements that rule.

SciPy/HiGHS solves this MILP in floating point. `solve_full_cup` requires a successful optimal status, requests zero relative MIP gap, reports the dual bound/gap, checks constraint residuals and integrality, and independently replays the resulting plan. This is a numerical global-optimization certificate to solver tolerances, NOT an exact rational proof. Time-limit termination raises SolverError, rather than falsely labeling an incumbent optimal.

## 7. Exact finite-action oracle

Specify finite sets of initial ratios, withdrawal volumes, and refill fractions. The exhaustive solver visits all budget-feasible words using Fraction arithmetic. Each withdrawal/refill is replayed and the final sample charged. Pruning only removes branches already infeasible by monotone inventory use or permanent pairwise separation violations. It never merges different sampled histories.

Therefore the least-radius complete word is a global optimum over exactly these finite choices. Secondary ties are resolved by largest separation, least total material, then lexicographic trajectory/actions. The MILP currently optimizes coverage only; its tied plan can differ.

An action grid is a restriction, not automatically a certified approximation to all continuous actions. No continuous-error bound follows from a small grid spacing alone when budgets are tight. The fresh relaxation gives a valid lower bound; a discrete feasible plan gives an upper bound. A gap between them remains a gap unless additional reasoning closes it.

The search has an upfront node-count bound. If it would exceed the requested maximum, it raises SearchLimitError before claiming any exhaustive result. Exponential enumeration is intended for small-instance verification and finite menus, not unlimited horizons.

## 8. Measurement errors: exact boxes and honest trajectory bounds

Three different notions must not be confused: fixed measuring increments, uncertain actual volumes, and an unknown relationship between composition and flavor.

### Composition-box result

If each actual sample independently lies in [l_i,u_i], its worst possible coverage is exactly

    max_{t in [0,1]} min_i max(t-l_i,u_i-t).

Proof: for fixed t the adversary can independently place each sample at its farther interval endpoint, simultaneously maximizing every individual distance. Maxima over t and sample positions commute. Each max(t-l_i,u_i-t) is a V-shaped piecewise-affine function. Their lower envelope is affine between intersections of constituent lines. It suffices to evaluate t=0,1 and all t=(l_i+u_j)/2. `box_worst_coverage` implements this finite exact calculation, including overlapping intervals.

If intervals are ordered and do not cross, the equivalent simpler expression is

    max(u_1, 1-l_N, (u_(i+1)-l_i)/2).

Marginal intervals along a sequential trajectory are generally correlated. Applying the independent-box result to them is a guaranteed upper bound, not automatically the true trajectory worst case.

### Full-cup uncertain volumes

Assume independent primitive intervals for initial composition, each actual withdrawal r_i, and each refill composition z_i. The actual replacement volume equals the actual withdrawal: this correlation is enforced physically. A pure-source refill has exact composition 0 or 1.

For x in [l,u], f=r/C in [f_l,f_u], z in [z_l,z_u], next x=(1-f)x+fz is multi-affine. Its extrema occur at corners. Recursively evaluating corners yields exact marginal composition intervals under the declared independent primitive-error model.

### When corner evaluation proves the worst coverage

Every chronological x_i is multi-affine in all primitive errors, as are component usages and pairwise differences x_i-x_j. Each uncertain input appears in one action only. A multi-affine function is a convex combination of its vertex values, so its extrema occur at vertices.

However, sorting compositions may change with errors, and coverage is NOT a single multi-affine function. Vertices alone do not universally prove its worst value. Counterexample: the two sample positions (0.1+0.8t,0.9-0.8t), t in [0,1], have radius 0.4 at t=0,1 but 0.5 at t=0.5.

We therefore verify that one chronological permutation is sorted at every uncertainty vertex. Each adjacent difference is multi-affine, so that order then holds throughout the box. Under this invariant order, coverage is a maximum of finitely many multi-affine endpoint/gap functions. The worst value IS attained at a vertex, giving an exact certificate.

If this test fails, the implementation reports:

    lower bound = greatest radius at any evaluated vertex
    upper bound = independent marginal-box worst radius.

It calls the answer exact only when the bounds coincide. Inventory maxima are separately exact at vertices, regardless of sorting. Minimum sample safety requires every withdrawal lower bound >=m. The final sample is a deterministic m in this model; final-withdrawal error is not silently ignored as though modeled.

### Finite-source robust optimization

For a fixed schedule of uncertain withdrawal intervals and a finite menu of source compositions, enumerate every source word. Exclude words that violate inventory or sample minimum for any allowed error. Each feasible word receives a certified lower/upper worst-coverage pair.

The minimum lower bound across all words bounds the global robust optimum from below. The smallest upper bound gives a feasible policy bounding it from above. Only equality sets `globally_certified=True`. This optimizes fixed open-loop source sequences, NOT measurement-dependent feedback policies. Systematic/shared calibration errors require a different joint uncertainty set; independence here must be a defensible modeling assumption.

### Useful simple perturbation guarantee

If each sample differs from nominal by at most epsilon, then absolute change in coverage is at most epsilon. Proof: for every target, each nearest-sample distance changes by at most epsilon; taking min and max preserves that bound. To guarantee nominally ordered samples remain separated by delta, a sufficient planned gap is delta+2epsilon. This is a useful coarse check, not a substitute for propagating actual volume errors.

## 9. Scope of what is solved

Implemented global results: exact unrestricted fresh solutions, numerical fresh LP including separation, numerical fixed-sip full-cup MILP, rational finite-action enumeration with variable withdrawals, and certified finite-source robust search.

Formulated but not claimed globally solved here: unrestricted continuous variable-volume or variable-withdrawal control; arbitrary mixed discrete/continuous equipment specifications; feedback control with imperfect observations; unknown sensory mappings. These problems are not silently approximated by the implemented subcases.

A physical flavor model could replace |x-y| with d_F(x,y). That changes the objective, not material conservation. Without sensory data or an explicit justified model, the code optimizes composition coverage only.

## References for numerical interfaces

The mathematics above is derived in this document. The external references describe solver behavior, not proof of our new formulas:

- SciPy `linprog`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html
- SciPy `milp`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html
- SciPy HiGHS options: https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html

Executed runtime versions are recorded in results/examples.json. Documentation version and executed library version need not be the same.
