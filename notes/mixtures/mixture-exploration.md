# The mathematics of tasting every possible mixture

> Type: reference
> Status: needs-review
> Updated: 2026-11-13
> Tags: mathematics, optimization, experimental-design, python

Two drinks, one mixing cup, and a limited supply of each. How should you pour
and taste them to explore as many different mixtures as possible?

Preparing each recipe in a clean cup is one problem. Keeping liquid in the cup,
taking a sip, and topping it up is another. That leftover liquid makes the order
of operations matter.

The useful question is not literally “Can I taste every mixture?” There are
infinitely many ratios. It is: **how close can every possible ratio be to one
of the mixtures I actually taste?**

## Define what “different” means

Let `x` be the fraction of ingredient A. Pure B is 0, equal parts is 0.5,
and pure A is 1. For tasted ratios `X`, define the coverage radius:

```text
R(X) = max over t in [0,1] of min over x in X of |t - x|.
```

It is the worst distance from a target ratio to the nearest tasted ratio.
Smaller is better. If the sorted samples are `y₁ ≤ … ≤ yₙ`, we can calculate it
exactly from the endpoints and gaps:

```text
R = max(y₁, 1 − yₙ, (y₂ − y₁)/2, …, (yₙ − yₙ₋₁)/2).
```

This measures **composition**, not flavor. A one-percentage-point recipe change
need not produce a perceptible or equally sized change in taste.

There are also different optimization goals. Minimizing the largest uncovered
gap is not the same as maximizing the number of distinct recipes. A coverage
optimizer can legitimately return duplicates when ingredients are scarce.
Requiring a positive separation between recipes is a separate constraint.

## The clean-cup benchmark

Suppose we can prepare `N` independent samples, each of minimum volume `m`.
We may measure arbitrary proportions and empty the cup between samples. If
there is enough of both ingredients, the best ratios are the midpoints:

```text
yᵢ = (2i − 1)/(2N),    R* = 1/(2N).
```

Why? A sample can cover at most an interval of length `2R`. To cover the unit
interval with `N` samples, `2NR ≥ 1`. Equally spaced midpoints attain that bound.

Six samples therefore have an ideal coverage radius of `1/12`, about 8.33
percentage points. Their A percentages are 8.33, 25, 41.67, 58.33, 75, and 91.67.
They use `Nm/2` of each ingredient.

Scarcity changes the answer. Let `a=A₀/m`, `b=B₀/m`, and `q=min(a,b)`.
For feasible `N` with `a+b ≥ N`, and without mandatory endpoints or a positive
separation requirement, the attached derivation gives:

```text
R* = max(1/(2N), max over k=1,…,N of (k − q)/k²).
```

The [theory note](theory.md) gives the constructive proof, including why
the bound is attainable. It also treats pure-endpoint and separated-sample
variants. Those are different contracts, not optional wording around one formula.

![Exact fresh-sample coverage frontier as the scarce ingredient budget changes.](figures/03_scarcity_frontier.png)

## A cup with memory

Now every taste begins with a full cup of capacity `C`. We withdraw `s`,
then replace exactly that volume with a refill whose A fraction is `z`.
After complete stirring:

```text
x_next = (1 − s/C)x + (s/C)z.
```

A sip by itself does not change the remaining composition. The refill moves
the current ratio toward `z`; it does not set the cup to `z`.

This also explains a physical limitation: partial replacements cannot remove
the last trace of an ingredient in finitely many steps. Visiting both pure
endpoints requires a full emptying or some operation outside this model.

## A greedy strategy can lose

Consider this illustrative problem, not a prescription for a real tasting:

- A 100 mL cup, initially half A and half B.
- Six tastes of 25 mL.
- Supplies of 125 mL A and 100 mL B, including the initial fill.
- Five top-ups, each using pure A or pure B.
- No refill after the last taste.

Both compared plans consume 150 mL and leave 75 mL in the cup. The budgets
require three A refills and two B refills, so there are only ten feasible words.

A specified myopic policy picks the feasible next action with the best current
coverage, breaking ties by separation, material use, and then the smaller ratio.
It chooses `B,A,A,A,B`. Exhaustive rational enumeration chooses `B,B,A,A,A`.

| Plan | Refill sequence | Coverage radius |
| --- | --- | --- |
| Myopic greedy policy | B, A, A, A, B | 3/8 = 0.375 |
| Exact best pure-source plan | B, B, A, A, A | 621/2048 = 0.30322265625 |

That is a **19.140625% reduction** in worst uncovered composition distance.
It disproves optimality of this particular greedy policy, not every heuristic.

![The six tastes in chronological order for greedy and globally planned refills.](figures/01_chronological_plans.png)

![Distance from each possible ratio to the nearest tasted ratio.](figures/02_coverage_distance.png)

The clean-cup result `1/12` is a useful lower bound, but not a fair replacement
policy under these rules: it removes the full-cup and fixed-first-mixture
constraints and leaves no residual liquid.

## Measurement error is more than an error bar

A nominal 25 mL sip with ±1 mL uncertainty may deliver only 24 mL. That already
fails a 25 mL minimum. Refilling the actual removed volume can also exceed
the nominal ingredient budget.

The supplied robust example instead allows actual intermediate withdrawals
of 25–27 mL, with supplies of 131 mL A and 104 mL B. Its final 25 mL taste is
modeled as exact. For the same `B,B,A,A,A` word, the reported worst-case
coverage is `396117/1280000 ≈ 0.3094664`.

That certificate depends on the stated independent-error model and a proof
that the sorting order remains unchanged throughout its uncertainty box.
Checking a few corners is not generally enough: if the order can change,
an interior error combination can be worse than every corner.

![Marginal composition bounds for the bounded-error plan, not one simultaneously attainable trajectory.](figures/04_bounded_error_plan.png)

## What is proved, and what is merely computed?

The distinction is worth keeping:

- The fresh-sample formulas have analytical derivations.
- Finite action menus can be exhaustively enumerated using exact fractions.
- The fixed-sip full-cup problem has a mixed-integer linear formulation;
  a successful floating-point solver result is subject to its tolerances.
- The uncertainty certificate applies only under its declared assumptions.
- Plots help explain these results. They are not proofs by themselves.

This does not solve unrestricted continuous variable-withdrawal control,
feedback with imperfect observations, or sensory flavor perception. Perfect
mixing, additive volume, and no evaporation, spillage, or cup residue are
assumptions throughout.

## Reproduce the work

The source and tests from the supplied v0.3 kit are retained here without its
wheel or raw test-output dumps. Python 3.12+ is required.

From the repository root:

```sh
python -m venv .venv-mixtures
. .venv-mixtures/bin/activate
python -m pip install -e ./notes/mixtures/experiment pytest
python -m pytest tests/mixtures
python -m mixture_explorer --help
```

On Windows, activate `.venv-mixtures\Scripts\Activate.ps1` instead.

The original kit reported 303 passing tests on Python 3.13.5, NumPy 2.3.5,
and SciPy 1.17.0. That is retained provenance, not a claim that those exact
versions ran here. This intake has not established a clean Ruff or strict
Pyright run. See [intake verification](verification.md) for checks actually
performed while adding this note.

Source: user-supplied `mixture_publication_kit_repacked(2).zip`, SHA-256
`fe9ee76a281a87528c93799274989ac2a701323cf004187c0aec0c4ea747bcbe`.
The figures are supplied outputs; they have not been regenerated for this intake.

## The takeaway

The interesting part is not the drinks. It is the distinction between choosing
a good set of experiments and finding a feasible sequence that actually reaches
them. Limited resources, carryover, and uncertainty turn a simple mixing
question into a small but useful lesson in experimental design.
