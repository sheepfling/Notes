# Cursed Macros, Part 4: Where to Stop

> Type: reference
> Status: needs-review
> Updated: 2026-11-20
> Tags: cpp, preprocessor, reflection, arrays

The old macro experiment recorded types, names, defaults, bounds, help text, and even dimensions for one- and two-dimensional arrays. Once I had that list, it was tempting to make it do everything. But a field list that knows an array has four slots doesn't know whether the fifth value in an incoming message is an error, whether to truncate it, or what the first four values mean. That's not a missing macro. That's a design decision.

## Get the shape from the type

If you're tempted to add an array-length column, see if the compiler already has the answer. Here's a complete C++17 example:

```cpp
#include <cassert>
#include <cstddef>
#include <iostream>
#include <type_traits>

struct Sample {
    int pixels[2][3]{};
    unsigned exposure_ms{20};
};

template<class T, std::size_t N>
constexpr auto outer_extent(const T (&)[N]) noexcept -> std::size_t {
    return N;
}

template<class T>
void describe(T* pixels) {
    // A pointer to the first row no longer carries the row count.
    static_assert(std::extent_v<T> == 3);
    std::cout << "Columns still in row type: " << std::extent_v<T> << '\n';
    assert(pixels[0][0] == 0);
}

bool valid_exposure(const Sample& sample) noexcept {
    return sample.exposure_ms >= 1 && sample.exposure_ms <= 1000;
}

int main() {
    Sample s;
    using Pixels = decltype(s.pixels);
    static_assert(std::rank_v<Pixels> == 2);
    static_assert(std::extent_v<Pixels, 0> == 2);
    static_assert(std::extent_v<Pixels, 1> == 3);
    static_assert(outer_extent(s.pixels) == 2);

    describe(s.pixels);
    assert(valid_exposure(s));
    s.exposure_ms = 0;
    assert(!valid_exposure(s));
}
```

```sh
c++ -std=c++17 -Wall -Wextra -Werror -pedantic example.cpp -o example
./example
```

```text
Columns still in row type: 3
```

The array reference preserves both dimensions; a pointer to the first row keeps only the row type, `int[3]`. That's why `sizeof` can measure an actual array at its declaration but cannot recover the original length from a pointer. For `std::array`, use its `.size()` or `std::tuple_size` on the container type instead.

## A bound in a table is not a check

`exposure_ms{20}` supplies a default. It does not prevent a parser from assigning zero. Likewise, a text help string can describe milliseconds, but it cannot prevent someone from passing seconds. I'd enforce rules at the input boundary, with a validator that reports what couldn't be admitted, or a domain type whose construction enforces the invariant. A cross-field rule (exposure must fit inside the frame period) belongs where both fields are visible. The field table can drive help and documentation without being the place where the application decides what is valid.

## Reach for the smallest tool that solves the duplication

| Situation | What I'd use |
|---|---|
| One small enum needs a declaration and a text mapping | A narrow X-macro table, with tests for spelling, invalid values, and aliases |
| An existing struct needs a visitor or a small set of labels | A typed descriptor table using pointers to members (typically a tuple if field types differ), or explicit code |
| A versioned format has several consumers or languages | A schema and generated adapters, with wire IDs, units, migration rules, and validation kept explicit |
| You need to inspect C++ declarations with a toolchain that implements language reflection | Evaluate [WG21's C++26 reflection design](https://www.open-std.org/jtc1/SC22/wg21/docs/papers/2025/p2996r13.html). Language reflection can inspect declarations; it doesn't decide your wire compatibility or validation policy |

A macro that generates a struct and its field visitor can be a net win. A macro that needs to explain why it selected the wrong constructor or produced a different shape on another compiler is harder to justify. My stopping point: use macros to repeat declarations and mappings, then hand the work back to typed C++ before it starts interpreting values.

[Back to the series](cursed-macros-series.md)
