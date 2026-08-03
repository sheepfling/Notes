# Validation Record

> Type: validation record  
> Status: current  
> Updated: 2026-08-01

This packet was assembled on Linux x86-64.

## C++

The portable C++ implementation was compiled and tested in three local
configurations:

| Compiler/configuration | Result |
| --- | --- |
| GCC 14.2, C++23, Release | Build passed; tests passed; 48 type rows emitted; no internal-consistency failures. |
| Clang 17, C++23, Release | Build passed; tests passed; 48 type rows emitted; no internal-consistency failures. |
| Clang 17, Debug, ASan + UBSan | Build passed; tests passed; report execution passed; no sanitizer finding. |

The optional undefined-behavior target was also compile-checked with GCC 14.2,
but it was not executed as part of portable validation.

## Python tooling

The report runner and comparison script passed Python bytecode compilation. The
C++-only workflow completed successfully. The comparison script was exercised
against a temporary schema-compatible Odin fixture to validate parsing,
fixed-width pairing, promotion reporting, and Markdown generation.

## Odin

The local assembly environment did not provide an Odin compiler. Therefore:

- the Odin source was reviewed against the current language and intrinsic
  documentation;
- an Odin test suite is included;
- GitHub Actions installs the pinned `dev-2026-07a` compiler, runs `odin test`,
  emits the report, and performs the cross-language comparison;
- no local Odin compile or runtime result is claimed in this packet.

The absence of a local compiler is intentionally visible instead of being hidden
behind a fabricated sample report.
