# Cursed macros: a short C++ series

> Type: reference
> Status: needs-review
> Updated: 2026-11-20
> Tags: cpp, macros, reflection, metaprogramming

Sometimes two pieces of C++ need to agree on the same list of names. Changing a
field in one place and forgetting a printer, lookup table, or parser is easy.
These posts start with a field list that fixes that problem and end with the
point where I would rather write ordinary C++.

Read in order, or jump to the problem you have. Each post explains its own
example; there is no shared header to install.

1. [One field list, two views of a struct](cursed-macros-struct-reflection.md):
   produce declarations and a typed visitor from the same rows. The C++17
   example checks defaults and exact output.
2. [Enum tables that agree](cursed-macros-enum-tables.md): keep explicit values
   and name lookups together, and decide what an alias means before exposing a
   reverse lookup.
3. [Variadic dispatch and the empty-argument trap](cursed-macros-variadic-dispatch.md):
   inspect the actual expansion, then use C++20's `__VA_OPT__` where forwarding
   optional arguments really helps.
4. [Where to stop](cursed-macros-where-to-stop.md): compare the macro approach
   with explicit typed metadata and decide when a schema, code generator, or
   compiler reflection makes more sense.

The common rule: use the preprocessor for the few tokens that must be repeated.
Keep the behavior, tests, and compatibility rules in typed code.
