# Cursed Macros, Part 3: Counting commas, picking a macro

> Type: reference
> Status: needs-review
> Updated: 2026-11-20
> Tags: cpp, preprocessor, variadic-macros

[Series index](cursed-macros-series.md) · [Part 2: Enum tables](cursed-macros-enum-tables.md) · [Part 4: Where to stop](cursed-macros-where-to-stop.md)

Two bugs can look like one. A selector returns the right macro name, but nothing happens. Add the missing call parentheses, and suddenly the selector picks the wrong name. The first bug is about **invocation**. The second is about **commas**. Neither has anything to do with C++ overload resolution: the compiler has not seen the call yet.

## Two layers for `#` and `##`

```cpp
#define SPELL_RAW(x) #x
#define SPELL(x) SPELL_RAW(x)
#define JOIN_RAW(a, b) a ## b
#define JOIN(a, b) JOIN_RAW(a, b)
#define CHANNEL 7

constexpr char raw[] = SPELL_RAW(CHANNEL); // "CHANNEL"
constexpr char expanded[] = SPELL(CHANNEL); // "7"
constexpr int JOIN(channel_, CHANNEL) = 42; // channel_7
```

Direct stringification preserves the argument's token spelling (with whitespace normalization). A parameter adjacent to `##` likewise is not macro-expanded first. In the outer wrappers the arguments are ordinary parameters, so `CHANNEL` becomes `7` before passing through to the inner operation. Token pasting makes **one preprocessing token**, not a phrase; the result must be valid. It is then eligible for rescanning. See the [working draft, macro replacement](https://eel.is/c++draft/cpp.replace).

## A selector is not a call

Pick a simple target: emit a test value with zero, one, or two components. The numbered macros produce ordinary C++; the preprocessor just chooses which one to invoke.

```cpp
#define DEMO_JOIN_RAW(a, b) a ## b
#define DEMO_JOIN(a, b) DEMO_JOIN_RAW(a, b)
#define DEMO_PICK(_1, _2, n, ...) n
#define DEMO_COUNT(...) DEMO_PICK(__VA_OPT__(__VA_ARGS__,) 2, 1, 0)

#define DEMO_VALUE_0() 0
#define DEMO_VALUE_1(x) (x)
#define DEMO_VALUE_2(x, y) (10 * (x) + (y))

#define DEMO_SELECT(...) DEMO_JOIN(DEMO_VALUE_, DEMO_COUNT(__VA_ARGS__))
#define DEMO_VALUE(...) DEMO_SELECT(__VA_ARGS__)(__VA_ARGS__)

static_assert(DEMO_VALUE() == 0);
static_assert(DEMO_VALUE(4) == 4);
static_assert(DEMO_VALUE(4, 2) == 42);
```

The selector slides a fixed tail under `DEMO_PICK`'s third parameter: `DEMO_PICK(2, 1, 0)` chooses `0`, `DEMO_PICK(4, 2, 1, 0)` chooses `1`, and `DEMO_PICK(4, 2, 2, 1, 0)` chooses `2`. `DEMO_SELECT(4, 2)` alone becomes the bare `DEMO_VALUE_2`; a function-like macro name is not expanded unless it is followed by `(`. `DEMO_VALUE(4, 2)` supplies that argument list, so rescanning turns it into `(10 * (4) + (2))`.

This helper has a contract: **zero to two nonempty, comma-safe arguments**, with an empty token list for zero. Give it a third argument and that argument lands in `n`, possibly choosing a nonsense token. There is no out-of-range check. Empty slots are not a feature: `DEMO_COUNT(,)` produces `2`, but `DEMO_VALUE(,)` feeds missing operands to C++. If you need real overloading and the macro is not doing token work, let functions and templates do it.

## Empty, omitted, and really two slots

```cpp
#define NO_TOKENS
#define NOTE(name, ...) emit(name __VA_OPT__(,) __VA_ARGS__)

// Preprocessor output is on the right:
NOTE("ready")            // emit("ready")
NOTE("ready", )          // emit("ready")
NOTE("ready", NO_TOKENS) // emit("ready")
NOTE("ready", 2, 3)      // emit("ready", 2, 3)
```

`__VA_OPT__` is standard C++20. It inserts its contents only if the variadic replacement has tokens. The first call omits the tail; the second supplies an empty tail; the third supplies a macro that expands to no tokens. `__VA_OPT__` sees all three as empty. An empty string literal (`""`) is still a token, and even a comma by itself is a token. The operator does **not** validate the resulting C++ or silently clean up empty slots.

A literal comma outside `__VA_OPT__` stays behind when the tail is empty. In a wrapper around `DEMO_COUNT`, `#define BAD_COUNT(...) DEMO_COUNT(9, __VA_ARGS__)` makes `BAD_COUNT()` expand as `DEMO_COUNT(9,)`, and that chooses `2`, not `1`. Write `DEMO_COUNT(9 __VA_OPT__(,) __VA_ARGS__)` when forwarding this kind of optional tail. Do not confuse standard `__VA_OPT__` with GNU's legacy `, ##__VA_ARGS__` extension, which in the named-parameter case distinguishes omission from an explicitly empty argument. See [WG21 P0306R4](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2017/p0306r4.html) and the [GCC preprocessor manual](https://gcc.gnu.org/onlinedocs/cpp/Variadic-Macros.html).

## Angle brackets do not hide a comma

```cpp
#include <utility>
#define MEMBER(type, name) type name;

using Coordinates = std::pair<int, int>;
struct Record { MEMBER(Coordinates, location) };

// Rejected: the preprocessor finds three arguments, not two.
// struct Broken { MEMBER(std::pair<int, int>, location) };
```

Macro argument splitting tracks nested parentheses, not template angle brackets, braces, or square brackets. The alias makes the type a single unambiguous argument. Extra parentheses can hide a comma in an expression, but `MEMBER((std::pair<int, int>), location)` is not a drop-in fix: this macro would emit those parentheses in front of the member name. Give the type a name instead of adding a general-purpose unparenthesizing macro.

## Ask the preprocessor before asking the compiler

```sh
c++ -std=c++20 -E -P demo.cpp
c++ -std=c++20 -pedantic-errors -fsyntax-only demo.cpp
```

`-E` stops after preprocessing; Clang and GCC accept `-P` to suppress line markers. Put the shortest reproducer in its own file, ideally without includes, and check what disappeared, which macro name survived, and where a comma landed. Then compile the usual code with warnings enabled. A missing invocation and a stray comma can look alike in a compiler diagnostic, but they leave different tokens on the page.

The right test set for a macro like this is small: zero, one, and maximum arity; omitted and explicitly empty tails; a macro that expands empty; and one comma-containing type. If those cases are hard to explain without drawing a flowchart, reconsider whether the macro belongs in the interface.
