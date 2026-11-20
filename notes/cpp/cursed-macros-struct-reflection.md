# Cursed macros: one field list, two views of a C++ struct

> Type: reference
> Status: needs-review
> Updated: 2026-11-20
> Tags: cpp, macros, reflection, metaprogramming

A struct is easy to change. Finding every string table, debug printer, and serialization helper that needs the same change is the annoying part. An X-macro makes that list explicit: write the fields once, then hand each entry to a different macro depending on what needs to be generated. The name comes from the conventional callback `X`; there is no special compiler feature behind it.

I went back to an old experiment that used `DEFINE_STRUCT` and `GET_STRUCT` to build declarations, defaults, and a printer from one list. The interesting part is smaller than that experiment: the preprocessor can hand C++ the field names it would otherwise need a separate registration list to know. C++ can do the work from there.

## The field list

Here is a self-contained C++17 example. The struct declarations and the visitor call sites come from the same three rows. The visitor body is ordinary typed C++.

```cpp
#include <cassert>
#include <iostream>
#include <sstream>
#include <string_view>

#define SENSOR_FIELDS(X) \
    X(int, channel, 0) \
    X(double, gain, 1.0) \
    X(bool, enabled, false)

#define DECLARE_FIELD(type, name, initial) type name = initial;
struct Sensor {
    SENSOR_FIELDS(DECLARE_FIELD)
};
#undef DECLARE_FIELD

#define VISIT_FIELD(type, name, initial) visitor(#name, sensor.name);
template <class Visitor>
void visit_fields(const Sensor& sensor, Visitor&& visitor) {
    SENSOR_FIELDS(VISIT_FIELD)
}
#undef VISIT_FIELD
#undef SENSOR_FIELDS

int main() {
    const Sensor defaults;
    assert(defaults.channel == 0);
    assert(defaults.gain == 1.0);
    assert(!defaults.enabled);

    const Sensor sensor{3, 1.5, true};
    std::ostringstream output;
    output << std::boolalpha;
    visit_fields(sensor, [&](std::string_view name, const auto& value) {
        output << name << '=' << value << '\n';
    });
    assert(output.str() == "channel=3\ngain=1.5\nenabled=true\n");
    std::cout << output.str();
}
```

The first pass turns `X(double, gain, 1.0)` into `double gain = 1.0;`. The second turns it into `visitor("gain", sensor.gain);`. The `#` operator stringifies the field token, but `sensor.gain` is a real member access: the compiler still type-checks it and the visitor sees a `double`. The visitor takes the source by const reference and does not copy the fields. Add one row and both passes see it.

The same trick works with enums. A list of names and explicit values can generate the enum declaration and a name lookup table. Count rows, not numeric values: enum constants can be sparse, and aliases may share a value. If aliases matter, decide whether numeric-to-name lookup chooses one canonical name or deliberately returns multiple names.

## Where it gets cursed

- **Commas are syntax.** `X(std::array<int, 3>, samples, {})` is split at the comma inside the angle brackets. Use a type alias. Likewise, a braced initializer does not shield commas; an expression in parentheses does.
- **A declaration shape is a contract.** `type name = initial;` does not describe every field syntax; a C-style array declarator, for example, needs a different shape or an alias. Existing or unlisted types do not gain reflection.
- **Optional arguments are a trap.** Forwarding a comma followed by empty `__VA_ARGS__` can leave an empty argument that breaks an arity selector. C++20's `__VA_OPT__(,)` can emit a separator only for nonempty variadic arguments. It does not turn a fixed-arity selector into an arbitrary-arity one. I would keep the field list fixed-width unless a real consumer needs otherwise.
- **A C++ name is not a stable external ID.** Renaming or reordering a field changes the names or order passed to this visitor. Keep wire names, IDs, compatibility rules, and validation explicit rather than treating a member dump as a format.
- **Macros leak.** Definitions do not respect C++ namespaces. Prefix any table macros that must escape their source file, and undefine short-lived helpers.

When an expansion gets weird, run the preprocessor instead of guessing. With this snippet saved as `example.cpp`:

```sh
c++ -std=c++17 -Wall -Wextra -Werror -pedantic example.cpp -o example
./example
c++ -std=c++17 -E -P example.cpp | sed -n '/^struct Sensor {/,+5p'
```

The run prints `channel=3`, `gain=1.5`, and `enabled=true`, one per line. The assertions check the defaults and that the visitor prints the expected field names, values, and order.

## When I would keep it

I like this for a small set of declarations I own, when at least two consumers really do need the same field list. For one printer or a few fields behind a stable interface, I would write the calls by hand. If the type already exists, a typed list of names and pointers-to-members is often easier to debug. An external schema with several language targets is a better candidate for code generation. For compiler-derived metadata in newer C++, WG21's [reflection paper](https://www.open-std.org/jtc1/SC22/wg21/docs/papers/2025/p2996r13.html) describes a different approach; this example needs only C++17.

References: [GCC preprocessor manual: variadic macros](https://gcc.gnu.org/onlinedocs/cpp/Variadic-Macros.html) and [stringification](https://gcc.gnu.org/onlinedocs/cpp/Stringizing.html).
