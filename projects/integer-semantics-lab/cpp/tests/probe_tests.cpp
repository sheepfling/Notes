#include "integer_semantics/probe.hpp"

#include <iostream>
#include <limits>
#include <string_view>

namespace {

[[nodiscard]] auto expect(const bool condition, const std::string_view message) -> bool {
    if (!condition) {
        std::cerr << "FAIL: " << message << '\n';
        return false;
    }
    return true;
}

}  // namespace

int main() {
    using integer_semantics::checked_add;
    using integer_semantics::checked_subtract;
    using integer_semantics::discover_signedness;
    using integer_semantics::inspect_type;
    using integer_semantics::integer_to_string;

    bool passed = true;

    passed &= expect(checked_add<unsigned int>(0U, 1U).value == 1U, "unsigned add value");
    passed &= expect(!checked_add<unsigned int>(0U, 1U).overflow, "unsigned add no overflow");
    passed &= expect(
        checked_add<unsigned int>(std::numeric_limits<unsigned int>::max(), 1U).overflow,
        "unsigned max plus one overflow"
    );
    passed &= expect(checked_subtract<unsigned int>(0U, 1U).overflow, "unsigned zero minus one overflow");

    passed &= expect(checked_add<int>(1, 2).value == 3, "signed add value");
    passed &= expect(!checked_add<int>(1, 2).overflow, "signed add no overflow");
    passed &= expect(
        checked_add<int>(std::numeric_limits<int>::max(), 1).overflow,
        "signed max plus one detected without execution"
    );
    passed &= expect(
        checked_subtract<int>(std::numeric_limits<int>::lowest(), 1).overflow,
        "signed min minus one detected without execution"
    );

    passed &= expect(
        integer_to_string(std::numeric_limits<long long>::lowest()) ==
            std::to_string(std::numeric_limits<long long>::lowest()),
        "signed decimal conversion"
    );
    passed &= expect(
        integer_to_string(std::numeric_limits<unsigned long long>::max()) ==
            std::to_string(std::numeric_limits<unsigned long long>::max()),
        "unsigned decimal conversion"
    );

    const auto signed_discovery = discover_signedness<int>();
    passed &= expect(signed_discovery.conclusive, "signed discovery conclusive");
    passed &= expect(signed_discovery.is_signed, "signed discovery value");

    const auto unsigned_discovery = discover_signedness<unsigned int>();
    passed &= expect(unsigned_discovery.conclusive, "unsigned discovery conclusive");
    passed &= expect(!unsigned_discovery.is_signed, "unsigned discovery value");

    const auto signed_report = inspect_type<int>("int", "test");
    passed &= expect(signed_report.signed_oracle, "signed oracle");
    passed &= expect(signed_report.observed_minus_one_is_negative, "signed converted minus one");
    passed &= expect(signed_report.observed_zero_minus_one_is_negative, "signed zero minus one");
    passed &= expect(signed_report.observed_complement_zero_is_negative, "signed complement zero");
    passed &= expect(signed_report.checked_add_overflow, "signed checked add overflow");
    passed &= expect(signed_report.checked_subtract_overflow, "signed checked subtract overflow");
    passed &= expect(!signed_report.direct_boundary_overflow_executed, "signed overflow not executed");
    passed &= expect(!signed_report.direct_signed_overflow_executed, "signed UB specimen isolated");
    passed &= expect(!signed_report.overflow_not_saturate, "signed direct overflow observation unavailable");
    passed &= expect(signed_report.internally_consistent, "signed report consistency");

    const auto unsigned_report = inspect_type<unsigned int>("unsigned int", "test");
    passed &= expect(!unsigned_report.signed_oracle, "unsigned signed oracle");
    passed &= expect(unsigned_report.unsigned_oracle, "unsigned oracle");
    passed &= expect(!unsigned_report.observed_minus_one_is_negative, "unsigned converted minus one");
    passed &= expect(!unsigned_report.observed_zero_minus_one_is_negative, "unsigned zero minus one");
    passed &= expect(!unsigned_report.observed_complement_zero_is_negative, "unsigned complement zero");
    passed &= expect(unsigned_report.maximum_plus_one == "0", "unsigned wrap value");
    passed &= expect(unsigned_report.checked_add_overflow, "unsigned checked add overflow");
    passed &= expect(unsigned_report.checked_subtract_overflow, "unsigned checked subtract overflow");
    passed &= expect(unsigned_report.direct_boundary_overflow_executed, "unsigned overflow executed");
    passed &= expect(unsigned_report.overflow_not_saturate, "unsigned non-saturating wrap");
    passed &= expect(unsigned_report.internally_consistent, "unsigned report consistency");

    const auto narrow_report = inspect_type<unsigned char>("unsigned char", "test");
    passed &= expect(!narrow_report.arithmetic_result_same_as_input, "narrow C++ promotion observed");
    passed &= expect(narrow_report.arithmetic_result_type == "int", "narrow C++ promotion target");

    const auto bool_report = inspect_type<bool>("bool", "test");
    passed &= expect(bool_report.special_boolean, "bool special category");
    passed &= expect(!bool_report.signed_oracle, "bool is not signed");
    passed &= expect(bool_report.unsigned_oracle, "std::is_unsigned_v<bool> is true");
    passed &= expect(bool_report.internally_consistent, "bool report consistency");

#if defined(__SIZEOF_INT128__)
    const auto signed_128 = inspect_type<__int128_t>("__int128_t", "test", false, true);
    const auto unsigned_128 = inspect_type<__uint128_t>("__uint128_t", "test", false, true);
    passed &= expect(signed_128.size_bytes == 16U, "signed 128-bit extension size");
    passed &= expect(signed_128.signed_oracle, "signed 128-bit extension oracle");
    passed &= expect(signed_128.internally_consistent, "signed 128-bit extension consistency");
    passed &= expect(unsigned_128.size_bytes == 16U, "unsigned 128-bit extension size");
    passed &= expect(!unsigned_128.signed_oracle, "unsigned 128-bit extension oracle");
    passed &= expect(unsigned_128.maximum_plus_one == "0", "unsigned 128-bit wrap");
    passed &= expect(unsigned_128.internally_consistent, "unsigned 128-bit extension consistency");
#endif

    return passed ? 0 : 1;
}
