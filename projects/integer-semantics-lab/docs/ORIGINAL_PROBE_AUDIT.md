# Original Odin Probe Audit

> Type: assessment  
> Status: historical  
> Updated: 2026-08-01

## Preserved intent

The original procedure was a compiler/language probe, not merely a replacement
for a signedness intrinsic. Its generic type parameter enabled the same
experiment to be instantiated over the entire integer catalog.

The modern pair preserves these ideas:

- test multiple independent semantic paths;
- inspect the compiled object representation;
- expose wrapping, saturation, or boundary behavior;
- retain unexpected observations instead of replacing them with a trait result;
- run the same probe over every selected language type.

## Branch-by-branch mapping

### Bitwise-not path

Original idea:

```text
all_ones = ~T{}
verify every byte is 255
return all_ones < 0
```

Modern implementation:

- retained in both languages;
- object bytes are included in the report;
- used as the preferred discovery path only when all bytes are `FF`.

### Zero-minus-one fallback

Original idea:

```text
underflow_value = zero - one
if result did not saturate to zero:
    return result < zero
```

Modern implementation:

- retained in both languages;
- C++ separately reports integral promotion and conversion back to `T`;
- direct expression remains safe for the tested standard types because the
  mathematical result is `-1`, although the evaluation type may differ.

### Maximum-plus-one fallback

Original idea:

```text
maximum_plus_one = maximum + one
if result differs from maximum:
    return result < maximum
```

Correction:

- retained as a boundary-behavior observation;
- removed as a signedness oracle because ordinary signed and unsigned wrapping
  can both yield a result below the maximum;
- evaluated directly by Odin;
- evaluated directly only for unsigned C++ types;
- moved into a separate opt-in UB lab for signed C++ specimens.

## Added modern probes

- compiler and target metadata;
- complete type catalogs rather than one ad hoc instantiation;
- explicit boolean and character-type treatment;
- endian-specific Odin integers;
- Odin distinct types;
- C++ aliases, promotions, and extensions;
- checked-overflow cross-checks;
- JSON Lines output and a cross-language comparison script;
- release-pinned continuous integration.
