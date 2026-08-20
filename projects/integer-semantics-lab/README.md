# Integer Semantics Lab — Odin and C++

> Type: project note  
> Status: needs-review  
> Updated: 2026-08-01

A pair of deliberately parallel language-inspection programs that exercise the
integer and boolean type systems of Odin and C++.

This is **not** primarily a utility for asking whether one type is signed. It is
an empirical language/compiler probe: instantiate a broad type catalog, observe
well-defined expressions and object representations, compare independent
signedness indicators, and emit a durable compiler/target report.

The project grew from an older Odin experiment that tried three discovery paths:

1. inspect `~0` and use `~0 < 0` when every object byte is `0xFF`;
2. fall back to `0 - 1` and test whether the result is negative;
3. inspect maximum-plus-one boundary behavior.

The first two paths can distinguish ordinary signed and unsigned integer
semantics. The third cannot: both signed and unsigned wrapping may produce a
value less than the maximum. This implementation retains maximum-plus-one as an
important boundary observation, but not as a signedness oracle.

## What both implementations report

Each selected type produces one JSON Lines record containing:

- type family, canonical type, alias/distinct/extension classification;
- size, alignment, object bits, and value bits;
- language-provided signedness oracles;
- observed `T(-1) < T(0)`, `(T(0) - T(1)) < T(0)`, and `(~T(0)) < T(0)`;
- whether every byte of `~T(0)` is `0xFF`;
- object bytes for zero, one, minus one, minimum, and maximum;
- minimum, maximum, and boundary arithmetic results;
- checked-overflow observations;
- expression-result type behavior;
- the signedness-discovery path and internal cross-check status.

A metadata record identifies the compiler, target, native byte order, build
mode, optimization mode, and sanitizer configuration where available.

## Intentional language differences

### Odin

The Odin probe directly evaluates integer boundary overflow because Odin defines
integer arithmetic overflow in terms of the signed or unsigned representation.
It also surveys:

- `bool`, `b8`, `b16`, `b32`, and `b64`;
- `rune`;
- `i8` through `i128` and their unsigned counterparts;
- `int`, `uint`, and `uintptr`;
- explicit little- and big-endian integer types;
- `byte` as an alias;
- user-defined distinct integer types.

### C++

The portable C++ probe never directly evaluates signed boundary overflow,
because that would have undefined behavior. It computes checked results without
performing the invalid expression and directly exercises wrapping only for
unsigned types.

It also reports integral promotions, implementation-selected `char` and
`wchar_t` signedness, standard aliases, and conditionally available `__int128`
extensions. `bool` is kept in its own logical category even though the standard
type traits classify it as integral and unsigned.

A separate, opt-in `cpp_integer_ub_lab` executable contains intentionally
undefined signed-overflow specimens. It is excluded from normal builds and must
not be used as a conformance oracle.

## Repository layout

```text
integer-semantics-lab/
├── cpp/
│   ├── include/integer_semantics/probe.hpp
│   ├── src/main.cpp
│   ├── tests/probe_tests.cpp
│   └── ub_lab/signed_overflow.cpp
├── odin/
│   ├── catalog.odin
│   ├── main.odin
│   ├── probe.odin
│   └── probe_test.odin
├── scripts/
│   ├── compare_reports.py
│   ├── run_lab.py
│   ├── run_all.sh
│   └── run_all.ps1
 ├── docs/original-signed-discovery.odin
├── docs/
├── sample_reports/
├── CMakeLists.txt
└── CMakePresets.json
```

## Build and run C++

Requirements: CMake 3.25+ and a C++23 compiler. Run these commands from the repository root.

```
cmake -S projects/integer-semantics-lab -B artifacts/integer-semantics-lab/build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build artifacts/integer-semantics-lab/build
ctest --test-dir artifacts/integer-semantics-lab/build --output-on-failure

./artifacts/integer-semantics-lab/build/cpp_integer_semantics --format=text --catalog=core
./artifacts/integer-semantics-lab/build/cpp_integer_semantics --format=jsonl --catalog=all  > artifacts/integer-semantics-lab/cpp.jsonl
```

On a multi-configuration generator, the executable may be under
`artifacts/integer-semantics-lab/build/Release/`.

### Intentionally undefined C++ specimens

Build, but do not treat as part of the portable probe:

```
cmake -S projects/integer-semantics-lab -B artifacts/integer-semantics-lab/build-ub  -DINTEGER_SEMANTICS_BUILD_UB_LAB=ON  -DINTEGER_SEMANTICS_BUILD_TESTS=OFF
cmake --build artifacts/integer-semantics-lab/build-ub --target cpp_integer_ub_lab
```

Run this target only in a deliberately selected compiler/flag matrix, preferably
with an undefined-behavior sanitizer or trapping configuration.

## Build and run Odin

Requirements: a current Odin compiler. The CI workflow pins `dev-2026-07a` so
published reports identify a reproducible compiler release.

```
odin test ./odin -define:ODIN_TEST_THREADS=1

odin run projects/integer-semantics-lab/odin -- --format=text --catalog=core
odin run projects/integer-semantics-lab/odin -- --format=jsonl --catalog=all  > artifacts/integer-semantics-lab/odin.jsonl
```

## Run both and compare

```
python projects/integer-semantics-lab/scripts/run_lab.py
```

On a machine without Odin, validate only C++ with:

```
python projects/integer-semantics-lab/scripts/run_lab.py --skip-odin
```

To compare existing reports:

```
python projects/integer-semantics-lab/scripts/compare_reports.py  artifacts/integer-semantics-lab/odin.jsonl  artifacts/integer-semantics-lab/cpp.jsonl  --output artifacts/integer-semantics-lab/comparison.md
```

The comparison intentionally matches only semantically corresponding fixed-width
types. Aliases and implementation extensions remain visible in their source
reports rather than being collapsed into a false one-to-one catalog.

## Command-line catalogs

### C++

```text
--format=text|jsonl
--catalog=core|all
--aliases
--extensions
```

`core` covers the standard fundamental integral and character types. `all` adds
standard aliases and available implementation extensions.

### Odin

```text
--format=text|jsonl
--catalog=core|all
--aliases
--endian
```

`core` covers Odin's boolean-width, rune, fixed-width, natural, and pointer-sized
integer types. `all` adds endian-specific, alias, and distinct-type probes.

## Validation status

- C++: compiled and tested locally with GCC 14.2 and Clang 17 in C++23 mode.
- C++: passed a Clang AddressSanitizer + UndefinedBehaviorSanitizer test build.
- Odin: source, tests, and CI are included; the local execution environment used
  to assemble this packet did not have an Odin compiler available, so local Odin
  compilation is not claimed.

See [Collection notes](NOTES.md), [Methodology](docs/METHODOLOGY.md), [Report schema](docs/SCHEMA.md),
[Original probe audit](docs/ORIGINAL_PROBE_AUDIT.md), and the detailed
[validation record](docs/VALIDATION.md).
