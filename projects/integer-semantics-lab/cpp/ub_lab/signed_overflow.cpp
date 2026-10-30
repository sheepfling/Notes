#include <cstdlib>
#include <iostream>
#include <limits>
#include <string_view>

// This executable is intentionally excluded from the default build.
// Every arithmetic operation selected below has undefined behavior in standard C++.
// Compile it under a specific compiler/flag/sanitizer matrix only as an implementation lab.

int main(const int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "Usage: cpp_integer_ub_lab <max-plus-one|min-minus-one|negate-min>\n";
        return 2;
    }

    const std::string_view specimen{argv[1]};
    volatile int value = 0;

    if (specimen == "max-plus-one") {
        volatile int maximum = std::numeric_limits<int>::max();
        value = maximum + 1;
    } else if (specimen == "min-minus-one") {
        volatile int minimum = std::numeric_limits<int>::lowest();
        value = minimum - 1;
    } else if (specimen == "negate-min") {
        volatile int minimum = std::numeric_limits<int>::lowest();
        value = -minimum;
    } else {
        std::cerr << "Unknown specimen: " << specimen << '\n';
        return 2;
    }

    std::cout << value << '\n';
    return 0;
}
