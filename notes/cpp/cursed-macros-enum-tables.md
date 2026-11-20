# Cursed Macros, Part 2: Counting Enums That Don't Count Up

> Type: reference
> Status: needs-review
> Updated: 2026-11-20
> Tags: cpp, preprocessor, x-macros, enums

I wanted to know the length of an enum at compile time. That sounds like a request for one number. Give the enum gaps and aliases, and suddenly there are at least three numbers: four declared names, three distinct values, and a largest value of nine. Which one do you want?

A single field list makes the choices visible. Here the first column is a C++ enumerator, the second is its numeric value, the third is the external spelling, and the fourth says whether that spelling is canonical on output.

```cpp
#include <array>
#include <cstddef>
#include <optional>
#include <string_view>

#define MODE_ROWS(X) \
    X(Off,         0, "off",          true)  \
    X(Warmup,      4, "warmup",       true)  \
    X(Ready,       9, "ready",        true)  \
    X(LegacyReady, 9, "legacy-ready", false)

#define ENUM_ROW(symbol, value, text, primary) symbol = value,
enum class Mode : unsigned { MODE_ROWS(ENUM_ROW) };
#undef ENUM_ROW

struct Entry {
    Mode value;
    std::string_view text;
    bool canonical;
};

#define TABLE_ROW(symbol, number, text, primary) Entry{Mode::symbol, text, primary},
constexpr auto entries = std::array{MODE_ROWS(TABLE_ROW)};
#undef TABLE_ROW
#undef MODE_ROWS

constexpr auto parse_mode(std::string_view text) -> std::optional<Mode> {
    for (const auto& row : entries)
        if (row.text == text) return row.value;
    return std::nullopt;
}

constexpr auto format_mode(Mode value) -> std::optional<std::string_view> {
    for (const auto& row : entries)
        if (row.value == value && row.canonical) return row.text;
    return std::nullopt;
}

constexpr auto valid_mapping() -> bool {
    for (const auto& row : entries) {
        std::size_t spellings = 0, canonical = 0;
        for (const auto& other : entries) {
            if (other.text == row.text) ++spellings;
            if (other.value == row.value && other.canonical) ++canonical;
        }
        if (row.text.empty() || spellings != 1 || canonical != 1) return false;
    }
    return true;
}

constexpr auto value_count() -> std::size_t {
    std::size_t count = 0;
    for (const auto& row : entries)
        if (row.canonical) ++count;
    return count;
}

static_assert(valid_mapping());
static_assert(entries.size() == 4 && value_count() == 3);
static_assert(parse_mode("ready") == Mode::Ready);
static_assert(parse_mode("legacy-ready") == Mode::Ready);
static_assert(format_mode(Mode::LegacyReady) == "ready");
static_assert(!parse_mode("READY"));
static_assert(!format_mode(static_cast<Mode>(8)));

int main() {}
```

Save the example as `enum.cpp` and run:

```sh
c++ -std=c++17 -Wall -Wextra -Werror -pedantic enum.cpp -o enum-demo
./enum-demo
```

The macros produce the declarations and table entries. Ordinary typed C++ owns the rules. The mapping check rejects duplicate spellings and requires exactly one canonical spelling per numeric value, so reordering rows does not change output. If you generated a switch with a case for every row, the two cases for nine would be ill-formed.

The enum value cannot tell you whether the original input was `ready` or `legacy-ready`. If you need to reproduce the original spelling, keep it separately. And if the numeric values or strings are an external format, treat changes to them as API changes, not incidental refactors. The macros don't grant compatibility.

[Back to the series](cursed-macros-series.md)
