# Methodology

> Type: reference  
> Status: current  
> Updated: 2026-08-01

## Purpose

The lab separates three questions that are easy to conflate:

1. **Language rule:** What does the language specification require?
2. **Implementation choice:** What did this compiler and target choose where the
   language permits variation?
3. **Observed representation:** What object bytes and expression results were
   produced in this particular run?

The output is evidence about a concrete compiler/target/build tuple. It is not a
claim that every implementation must have identical widths, aliases, character
signedness, object bytes, or extension types.

## Shared probes

For each ordinary integer type `T`, both implementations construct:

```text
zero            = T(0)
one             = T(1)
minus_one       = T(-1)
zero_minus_one  = zero - one
complement_zero = ~zero
minimum         = lowest representable T
maximum         = greatest representable T
```

The following independent observations are compared:

```text
minus_one < zero
zero_minus_one < zero
complement_zero < zero
all object bytes of complement_zero are 0xFF
language/compiler signedness oracle
```

The original discovery order is retained:

1. Prefer the bitwise-complement comparison only when its object representation
   is verified as all-one bytes.
2. Fall back to zero-minus-one when the first representation check is not usable.
3. Report maximum-plus-one behavior, but never infer signedness from it.

## Why maximum-plus-one is not a signedness oracle

Suppose a type has a maximum value `M` and boundary addition produces a wrapped
value `W`. For an ordinary modulo unsigned type, `W = 0`, so `W < M`. For a
signed two's-complement type with defined wrapping, maximum-plus-one produces the
minimum value, which is also less than `M`.

Therefore, the predicate

```text
(maximum + 1) < maximum
```

can detect non-saturating boundary behavior, but cannot by itself distinguish
signed from unsigned types.

## Boundary arithmetic

### Odin

The Odin implementation evaluates maximum-plus-one and minimum-minus-one
normally, then cross-checks the result with `intrinsics.overflow_add` and
`intrinsics.overflow_sub`.

### C++

The portable C++ implementation directly executes boundary arithmetic only for
unsigned types. For signed types it first checks whether the mathematical result
is representable and returns an overflow flag without evaluating an overflowing
built-in expression.

The optional C++ UB lab is physically separated from the portable probe and is
excluded by default.

## Expression typing

The same source-shaped expression can answer different questions in the two
languages.

Odin's explicitly typed integer arithmetic remains in the selected type. C++
may first apply integral promotion, so the probe reports the expression type of
`T{} - T{1}` separately from the result after conversion back to `T`.

## Object representation

Only initialized, trivially copyable values are inspected. The C++ implementation
uses `std::bit_cast` into `std::array<std::byte, sizeof(T)>`. The Odin
implementation transmutes the initialized value into `[size_of(T)]byte`.

The report labels these as observations. Except where the language explicitly
requires a property, a byte pattern is not promoted into a portable language
rule.

## Internal consistency

Each type row includes `internally_consistent`. This checks agreement among the
language oracle, safe expression observations, representation-assisted discovery,
and checked boundary results.

A failed row is not silently normalized. The test executable fails and the
comparison script exits nonzero so the complete conflicting record remains
available for diagnosis.
