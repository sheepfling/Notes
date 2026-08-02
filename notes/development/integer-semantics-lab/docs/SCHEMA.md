# JSON Lines Report Schema

> Type: reference  
> Status: current  
> Updated: 2026-08-01

The report is JSON Lines: one complete JSON object per line. The first object is
metadata. Remaining objects are type observations.

Schema version: `1`.

## Metadata record

Common fields:

| Field | Meaning |
|---|---|
| `record_kind` | Always `metadata`. |
| `schema_version` | Schema integer, currently `1`. |
| `language` | `Odin` or `C++`. |
| `compiler_version` | Compiler release/version string. |
| `os` | Target operating system. |
| `architecture` | Target architecture. |
| `native_endian` | Native byte order. |
| `optimization` | Build optimization description where available. |
| `sanitizers` | Active sanitizer configuration where available. |

Language-specific metadata is preserved rather than forced into misleading
values. C++ includes compiler name and language-standard macro. Odin includes
compiler hash, build mode, and debug state.

## Type record

`record_kind` is `integer_type` for both ordinary integers and the special
boolean rows so one consumer can load a single catalog.

### Identity and classification

| Field | Meaning |
|---|---|
| `language` | Producing language. |
| `label` | Catalog label used to instantiate the probe. |
| `family` | Human-readable type family. |
| `canonical_type` | Canonical/backing type description. |
| `is_alias` | Catalog entry is an alias. |
| `is_distinct` | Entry is a distinct nominal type. |
| `is_extension` | Entry is an implementation extension. |
| `special_boolean` | Row is a logical boolean rather than an ordinary integer probe. |

### Shape and oracles

| Field | Meaning |
|---|---|
| `size_bytes` | `sizeof`/`size_of`. |
| `alignment_bytes` | Required alignment. |
| `object_bits` | Eight times object size in this schema. |
| `value_bits` | Non-sign value bits reported by the language implementation. |
| `signed_oracle` | Primary language/library signedness classification. |
| `unsigned_oracle` | Primary unsigned classification. |
| `numeric_limits_signed` | C++ `numeric_limits<T>::is_signed`; `null` in Odin. |
| `numeric_limits_is_modulo` | C++ `numeric_limits<T>::is_modulo`; `null` in Odin. |

### Observations

| Field | Meaning |
|---|---|
| `observed_minus_one_is_negative` | Result of comparing converted `-1` with zero. |
| `observed_zero_minus_one_is_negative` | Result of the zero-minus-one probe. |
| `observed_complement_zero_is_negative` | Result of the bitwise-complement probe. |
| `complement_bytes_all_ff` | Whether every object byte of `~0` is `FF`. |
| `arithmetic_result_same_as_input` | Whether the subtraction expression's type remains the catalog type. |
| `arithmetic_result_type` | Human-readable expression result type. |
| `integer_endian` | Type-specific byte-order classification. |
| `overflow_semantics` | Language-specific description of the evaluated boundary behavior. |

### Values and object bytes

The following values are strings so 128-bit integers remain exact across JSON
consumers:

```text
minimum
maximum
zero_minus_one
complement_zero
maximum_plus_one
minimum_minus_one
```

Object-byte strings are uppercase hexadecimal bytes in memory order:

```text
bytes_zero
bytes_one
bytes_minus_one
bytes_minimum
bytes_maximum
```

### Boundary and discovery status

| Field | Meaning |
|---|---|
| `checked_add_overflow` | Checked maximum-plus-one overflow flag. |
| `checked_subtract_overflow` | Checked minimum-minus-one overflow flag. |
| `direct_boundary_overflow_executed` | At least one direct boundary expression was evaluated. |
| `direct_signed_overflow_executed` | Signed boundary overflow was directly evaluated. Always false in the portable C++ probe. |
| `underflow_not_saturate` | Zero-minus-one differs from zero. |
| `overflow_not_saturate` | Direct maximum-plus-one differs from maximum when directly executed. |
| `discovery_path` | `bitwise-not`, `zero-minus-one`, or an inconclusive path. |
| `discovery_conclusive` | Discovery produced a signedness result. |
| `internally_consistent` | All required cross-checks for this row agree. |

Fields that do not apply to a language or special type use JSON `null`, false,
or the explicit string `not applicable` according to their value category. The
comparison script does not infer missing facts from these placeholders.
