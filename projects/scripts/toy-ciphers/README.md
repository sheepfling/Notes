# Toy printable-text ciphers

> Type: experiment note  
> Status: needs-review  
> Updated: 2026-08-01

The older script export contained two reversible character transforms. They are useful for
thinking about modular arithmetic, key length, and round trips, but they are not cryptographic
implementations and must not be used to protect secrets.

## One-time-pad-shaped transform

[otp.py](otp.py) creates a random printable-ASCII key as long as the UTF-8 text input and adds
each key character modulo the 95 printable ASCII characters. Subtraction reverses the operation.
Newlines and non-ASCII characters are preserved, while the key still consumes one position for
each source character.

Run the self-test:

```
uv run python projects/scripts/toy-ciphers/otp.py test
```

For a file, provide explicit output paths so an experiment cannot silently overwrite the input:

```
uv run python projects/scripts/toy-ciphers/otp.py encrypt input.txt encrypted.txt key.txt
uv run python projects/scripts/toy-ciphers/otp.py decrypt encrypted.txt key.txt restored.txt
```

Despite its name, this is not a complete one-time pad system. It has no authenticated format,
binary support, key-distribution mechanism, metadata integrity, or protection against key reuse.
Use a vetted authenticated-encryption library for real data.

## Repeating-passphrase transform

[pcrypt.py](pcrypt.py) repeats a printable passphrase across the input. It is a compact
Vigenere-like exercise, not encryption. The cleaned version rejects empty or non-printable
passphrases and fails clearly instead of silently producing an empty or truncated result.

```
uv run python projects/scripts/toy-ciphers/pcrypt.py test
uv run python projects/scripts/toy-ciphers/pcrypt.py encrypt input.txt passphrase transformed.txt
uv run python projects/scripts/toy-ciphers/pcrypt.py decrypt transformed.txt passphrase restored.txt
```

Repeating keys are especially unsuitable for confidentiality because they create predictable
structure. The implementation also works on text only and does not authenticate the output.

## What changed during ingestion

- Fixed the original OTP self-test's missing `randint` import by replacing ad hoc randomness with
  `secrets` for key generation; this still does not make the file format secure.
- Rejected length mismatches instead of allowing `zip` to silently discard data.
- Rejected empty passphrases instead of allowing `cycle("")` to produce an empty output.
- Restricted the arithmetic to printable ASCII 32 through 126, matching the generated alphabet.
- Replaced permissive `parse_known_args` behavior with explicit command-line arguments.
- Kept the old line-display helper as a separate [readlines project](../readlines/README.md).

The focused tests cover printable and Unicode text, newlines, invalid keys, empty passphrases,
and the line-display helper. They test reversibility, not security.
