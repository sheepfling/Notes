#pragma once

#include <array>
#include <bit>
#include <climits>
#include <concepts>
#include <cstddef>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <ostream>
#include <sstream>
#include <string>
#include <string_view>
#include <type_traits>

namespace integer_semantics {

enum class output_format {
    text,
    jsonl,
};

template <typename T>
concept cpp_integral = std::integral<std::remove_cv_t<T>>;

template <typename T>
struct checked_result {
    T value{};
    bool overflow{};
    bool value_is_valid{};
};

struct signedness_discovery {
    bool is_signed{};
    bool conclusive{};
    std::string_view path{"inconclusive"};
};

[[nodiscard]] inline auto json_escape(const std::string_view value) -> std::string {
    std::ostringstream output;
    for (const char character : value) {
        const auto byte = static_cast<unsigned char>(character);
        switch (byte) {
            case '"':
                output << "\\\"";
                break;
            case '\\':
                output << "\\\\";
                break;
            case '\b':
                output << "\\b";
                break;
            case '\f':
                output << "\\f";
                break;
            case '\n':
                output << "\\n";
                break;
            case '\r':
                output << "\\r";
                break;
            case '\t':
                output << "\\t";
                break;
            default:
                if (byte < 0x20U) {
                    output << "\\u" << std::hex << std::setw(4) << std::setfill('0')
                           << static_cast<unsigned int>(byte) << std::dec;
                } else {
                    output << static_cast<char>(byte);
                }
                break;
        }
    }
    return output.str();
}

template <typename T>
[[nodiscard]] consteval auto canonical_type_name() -> std::string_view {
    using U = std::remove_cv_t<T>;

    if constexpr (std::same_as<U, bool>) {
        return "bool";
    } else if constexpr (std::same_as<U, char>) {
        return "char";
    } else if constexpr (std::same_as<U, signed char>) {
        return "signed char";
    } else if constexpr (std::same_as<U, unsigned char>) {
        return "unsigned char";
    } else if constexpr (std::same_as<U, wchar_t>) {
        return "wchar_t";
    } else if constexpr (std::same_as<U, char8_t>) {
        return "char8_t";
    } else if constexpr (std::same_as<U, char16_t>) {
        return "char16_t";
    } else if constexpr (std::same_as<U, char32_t>) {
        return "char32_t";
    } else if constexpr (std::same_as<U, short>) {
        return "short";
    } else if constexpr (std::same_as<U, unsigned short>) {
        return "unsigned short";
    } else if constexpr (std::same_as<U, int>) {
        return "int";
    } else if constexpr (std::same_as<U, unsigned int>) {
        return "unsigned int";
    } else if constexpr (std::same_as<U, long>) {
        return "long";
    } else if constexpr (std::same_as<U, unsigned long>) {
        return "unsigned long";
    } else if constexpr (std::same_as<U, long long>) {
        return "long long";
    } else if constexpr (std::same_as<U, unsigned long long>) {
        return "unsigned long long";
#if defined(__SIZEOF_INT128__)
    } else if constexpr (std::same_as<U, __int128_t>) {
        return "__int128_t";
    } else if constexpr (std::same_as<U, __uint128_t>) {
        return "__uint128_t";
#endif
    } else {
        return "implementation extension";
    }
}

[[nodiscard]] inline auto compiler_name() -> std::string_view {
#if defined(__clang__)
    return "Clang";
#elif defined(__GNUC__)
    return "GCC";
#elif defined(_MSC_VER)
    return "MSVC";
#else
    return "unknown";
#endif
}

[[nodiscard]] inline auto compiler_version() -> std::string {
#if defined(__clang__)
    return __clang_version__;
#elif defined(__GNUC__)
    return __VERSION__;
#elif defined(_MSC_FULL_VER)
    return std::to_string(_MSC_FULL_VER);
#else
    return "unknown";
#endif
}

[[nodiscard]] inline auto target_architecture() -> std::string_view {
#if defined(__x86_64__) || defined(_M_X64)
    return "x86_64";
#elif defined(__i386__) || defined(_M_IX86)
    return "x86";
#elif defined(__aarch64__) || defined(_M_ARM64)
    return "aarch64";
#elif defined(__arm__) || defined(_M_ARM)
    return "arm";
#elif defined(__riscv) && (__riscv_xlen == 64)
    return "riscv64";
#elif defined(__wasm64__)
    return "wasm64";
#elif defined(__wasm32__)
    return "wasm32";
#else
    return "unknown";
#endif
}

[[nodiscard]] inline auto operating_system() -> std::string_view {
#if defined(_WIN32)
    return "Windows";
#elif defined(__APPLE__)
    return "Darwin";
#elif defined(__linux__)
    return "Linux";
#elif defined(__FreeBSD__)
    return "FreeBSD";
#elif defined(__OpenBSD__)
    return "OpenBSD";
#elif defined(__NetBSD__)
    return "NetBSD";
#else
    return "unknown";
#endif
}

[[nodiscard]] inline auto native_endian_name() -> std::string_view {
    if constexpr (std::endian::native == std::endian::little) {
        return "little";
    } else if constexpr (std::endian::native == std::endian::big) {
        return "big";
    } else {
        return "mixed";
    }
}

[[nodiscard]] inline auto optimization_name() -> std::string_view {
#if defined(__OPTIMIZE_SIZE__)
    return "size";
#elif defined(__OPTIMIZE__)
    return "optimized";
#elif defined(_DEBUG)
    return "debug";
#else
    return "unoptimized-or-unknown";
#endif
}

template <typename T>
[[nodiscard]] auto bytes_hex(const T value) -> std::string {
    static_assert(std::is_trivially_copyable_v<T>);
    const auto bytes = std::bit_cast<std::array<std::byte, sizeof(T)>>(value);
    std::ostringstream output;
    output << std::hex << std::uppercase << std::setfill('0');
    for (std::size_t index = 0; index < bytes.size(); ++index) {
        if (index != 0U) {
            output << ' ';
        }
        output << std::setw(2) << std::to_integer<unsigned int>(bytes[index]);
    }
    return output.str();
}

template <typename T>
[[nodiscard]] auto all_bytes_are_ff(const T value) -> bool {
    static_assert(std::is_trivially_copyable_v<T>);
    const auto bytes = std::bit_cast<std::array<std::byte, sizeof(T)>>(value);
    for (const std::byte byte : bytes) {
        if (byte != std::byte{0xFF}) {
            return false;
        }
    }
    return true;
}

template <typename U>
[[nodiscard]] auto unsigned_to_decimal(U value) -> std::string {
    static_assert(std::is_unsigned_v<U>);

    std::array<char, static_cast<std::size_t>(std::numeric_limits<U>::digits10) + 4U> buffer{};
    auto cursor = buffer.end();
    do {
        const auto digit = static_cast<unsigned int>(value % U{10});
        *--cursor = static_cast<char>('0' + digit);
        value = static_cast<U>(value / U{10});
    } while (value != U{0});
    return {cursor, buffer.end()};
}

template <cpp_integral T>
[[nodiscard]] auto integer_to_string(const T value) -> std::string {
    using U = std::remove_cv_t<T>;
    if constexpr (std::same_as<U, bool>) {
        return value ? "true" : "false";
    } else {
        using unsigned_type = std::make_unsigned_t<U>;
        if constexpr (std::is_signed_v<U>) {
            if (value < U{0}) {
                unsigned_type magnitude = static_cast<unsigned_type>(value);
                magnitude = static_cast<unsigned_type>(unsigned_type{0} - magnitude);
                return "-" + unsigned_to_decimal(magnitude);
            }
        }
        return unsigned_to_decimal(static_cast<unsigned_type>(value));
    }
}

template <cpp_integral T>
[[nodiscard]] constexpr auto checked_add(const T lhs, const T rhs) noexcept
    -> checked_result<T> {
    if constexpr (std::same_as<T, bool>) {
        return {.value = false, .overflow = false, .value_is_valid = false};
    } else if constexpr (std::is_unsigned_v<T>) {
        const T value = static_cast<T>(lhs + rhs);
        return {
            .value = value,
            .overflow = value < lhs,
            .value_is_valid = true,
        };
    } else {
        constexpr T minimum = std::numeric_limits<T>::lowest();
        constexpr T maximum = std::numeric_limits<T>::max();

        if ((rhs > T{0} && lhs > static_cast<T>(maximum - rhs)) ||
            (rhs < T{0} && lhs < static_cast<T>(minimum - rhs))) {
            return {.value = T{}, .overflow = true, .value_is_valid = false};
        }
        return {
            .value = static_cast<T>(lhs + rhs),
            .overflow = false,
            .value_is_valid = true,
        };
    }
}

template <cpp_integral T>
[[nodiscard]] constexpr auto checked_subtract(const T lhs, const T rhs) noexcept
    -> checked_result<T> {
    if constexpr (std::same_as<T, bool>) {
        return {.value = false, .overflow = false, .value_is_valid = false};
    } else if constexpr (std::is_unsigned_v<T>) {
        return {
            .value = static_cast<T>(lhs - rhs),
            .overflow = lhs < rhs,
            .value_is_valid = true,
        };
    } else {
        constexpr T minimum = std::numeric_limits<T>::lowest();
        constexpr T maximum = std::numeric_limits<T>::max();

        if ((rhs > T{0} && lhs < static_cast<T>(minimum + rhs)) ||
            (rhs < T{0} && lhs > static_cast<T>(maximum + rhs))) {
            return {.value = T{}, .overflow = true, .value_is_valid = false};
        }
        return {
            .value = static_cast<T>(lhs - rhs),
            .overflow = false,
            .value_is_valid = true,
        };
    }
}

template <cpp_integral T>
[[nodiscard]] auto discover_signedness() -> signedness_discovery {
    using U = std::remove_cv_t<T>;
    if constexpr (std::same_as<U, bool>) {
        return {};
    } else {
        const U zero = U{0};
        const U one = U{1};
        const U complement_zero = static_cast<U>(~zero);
        if (all_bytes_are_ff(complement_zero)) {
            return {
                .is_signed = complement_zero < zero,
                .conclusive = true,
                .path = "bitwise-not",
            };
        }

        const U zero_minus_one = static_cast<U>(zero - one);
        if (zero_minus_one != zero) {
            return {
                .is_signed = zero_minus_one < zero,
                .conclusive = true,
                .path = "zero-minus-one",
            };
        }
        return {};
    }
}

struct type_report {
    std::string_view label;
    std::string_view family;
    std::string_view canonical_type;
    bool is_alias{};
    bool is_extension{};
    bool special_boolean{};
    std::size_t size_bytes{};
    std::size_t alignment_bytes{};
    int object_bits{};
    int value_bits{};
    bool signed_oracle{};
    bool unsigned_oracle{};
    bool numeric_limits_signed{};
    bool observed_minus_one_is_negative{};
    bool observed_zero_minus_one_is_negative{};
    bool observed_complement_zero_is_negative{};
    bool complement_bytes_all_ff{};
    bool arithmetic_result_same_as_input{};
    std::string_view arithmetic_result_type;
    bool numeric_limits_is_modulo{};
    std::string minimum;
    std::string maximum;
    std::string zero_minus_one;
    std::string complement_zero;
    std::string maximum_plus_one;
    std::string minimum_minus_one;
    std::string bytes_zero;
    std::string bytes_one;
    std::string bytes_minus_one;
    std::string bytes_minimum;
    std::string bytes_maximum;
    bool checked_add_overflow{};
    bool checked_subtract_overflow{};
    bool direct_boundary_overflow_executed{};
    bool direct_signed_overflow_executed{};
    bool underflow_not_saturate{};
    bool overflow_not_saturate{};
    signedness_discovery discovery{};
    bool internally_consistent{};
};

template <cpp_integral T>
[[nodiscard]] auto inspect_type(
    const std::string_view label,
    const std::string_view family,
    const bool is_alias = false,
    const bool is_extension = false
) -> type_report {
    using U = std::remove_cv_t<T>;
    constexpr bool special_boolean = std::same_as<U, bool>;

    type_report report{};
    report.label = label;
    report.family = family;
    report.canonical_type = canonical_type_name<U>();
    report.is_alias = is_alias;
    report.is_extension = is_extension;
    report.special_boolean = special_boolean;
    report.size_bytes = sizeof(U);
    report.alignment_bytes = alignof(U);
    report.object_bits = static_cast<int>(sizeof(U) * CHAR_BIT);
    report.value_bits = std::numeric_limits<U>::digits;
    report.signed_oracle = std::is_signed_v<U>;
    report.unsigned_oracle = std::is_unsigned_v<U>;
    report.numeric_limits_signed = std::numeric_limits<U>::is_signed;
    report.numeric_limits_is_modulo = std::numeric_limits<U>::is_modulo;
    report.minimum = integer_to_string(std::numeric_limits<U>::lowest());
    report.maximum = integer_to_string(std::numeric_limits<U>::max());
    report.bytes_zero = bytes_hex(U{0});
    report.bytes_one = bytes_hex(U{1});
    report.bytes_minimum = bytes_hex(std::numeric_limits<U>::lowest());
    report.bytes_maximum = bytes_hex(std::numeric_limits<U>::max());

    if constexpr (special_boolean) {
        report.arithmetic_result_type = "not applicable";
        report.zero_minus_one = "not applicable";
        report.complement_zero = "not applicable";
        report.maximum_plus_one = "not applicable";
        report.minimum_minus_one = "not applicable";
        report.bytes_minus_one = "not applicable";
        report.internally_consistent =
            !report.signed_oracle && report.unsigned_oracle &&
            !report.numeric_limits_signed;
        return report;
    } else {
        const U zero = U{0};
        const U one = U{1};
        const U minus_one = static_cast<U>(-1);
        const U zero_minus_one = static_cast<U>(zero - one);
        const U complement_zero = static_cast<U>(~zero);
        const auto maximum_add = checked_add(std::numeric_limits<U>::max(), one);
        const auto minimum_subtract = checked_subtract(std::numeric_limits<U>::lowest(), one);

        report.observed_minus_one_is_negative = minus_one < zero;
        report.observed_zero_minus_one_is_negative = zero_minus_one < zero;
        report.observed_complement_zero_is_negative = complement_zero < zero;
        report.complement_bytes_all_ff = all_bytes_are_ff(complement_zero);
        report.arithmetic_result_same_as_input = std::same_as<decltype(zero - one), U>;
        report.arithmetic_result_type = canonical_type_name<decltype(zero - one)>();
        report.zero_minus_one = integer_to_string(zero_minus_one);
        report.complement_zero = integer_to_string(complement_zero);
        report.maximum_plus_one = maximum_add.value_is_valid
            ? integer_to_string(maximum_add.value)
            : "not executed: signed overflow is undefined";
        report.minimum_minus_one = minimum_subtract.value_is_valid
            ? integer_to_string(minimum_subtract.value)
            : "not executed: signed overflow is undefined";
        report.bytes_minus_one = bytes_hex(minus_one);
        report.checked_add_overflow = maximum_add.overflow;
        report.checked_subtract_overflow = minimum_subtract.overflow;
        report.direct_boundary_overflow_executed = maximum_add.value_is_valid;
        report.direct_signed_overflow_executed = false;
        report.underflow_not_saturate = zero_minus_one != zero;
        report.overflow_not_saturate =
            maximum_add.value_is_valid && maximum_add.value != std::numeric_limits<U>::max();
        report.discovery = discover_signedness<U>();
        report.internally_consistent =
            report.discovery.conclusive &&
            report.discovery.is_signed == report.signed_oracle &&
            report.signed_oracle == report.numeric_limits_signed &&
            report.signed_oracle == report.observed_minus_one_is_negative &&
            report.signed_oracle == report.observed_zero_minus_one_is_negative &&
            report.signed_oracle == report.observed_complement_zero_is_negative &&
            report.underflow_not_saturate &&
            report.checked_add_overflow &&
            report.checked_subtract_overflow;
        return report;
    }
}

inline void write_metadata(std::ostream& output, const output_format format) {
    if (format == output_format::jsonl) {
        output << "{\"record_kind\":\"metadata\","
               << "\"schema_version\":1,"
               << "\"language\":\"C++\","
               << "\"language_level\":" << __cplusplus << ','
               << "\"compiler\":\"" << json_escape(compiler_name()) << "\","
               << "\"compiler_version\":\"" << json_escape(compiler_version()) << "\","
               << "\"os\":\"" << json_escape(operating_system()) << "\","
               << "\"architecture\":\"" << json_escape(target_architecture()) << "\","
               << "\"native_endian\":\"" << native_endian_name() << "\","
               << "\"optimization\":\"" << optimization_name() << "\","
               << "\"char_bit\":" << CHAR_BIT
               << "}\n";
        return;
    }

    output << "Integer Semantics Probe — C++\n"
           << "  language level : " << __cplusplus << '\n'
           << "  compiler       : " << compiler_name() << ' ' << compiler_version() << '\n'
           << "  target         : " << operating_system() << '/' << target_architecture() << '\n'
           << "  native endian  : " << native_endian_name() << '\n'
           << "  optimization   : " << optimization_name() << '\n'
           << "  CHAR_BIT       : " << CHAR_BIT << "\n\n";
}

inline void write_report(
    std::ostream& output,
    const type_report& report,
    const output_format format
) {
    const std::string_view overflow_semantics = report.special_boolean
        ? "not applicable"
        : (report.signed_oracle
               ? "undefined; direct signed overflow is not executed"
               : "defined modulo 2^N");

    if (format == output_format::jsonl) {
        output << '{'
               << "\"record_kind\":\"integer_type\","
               << "\"language\":\"C++\","
               << "\"label\":\"" << json_escape(report.label) << "\","
               << "\"family\":\"" << json_escape(report.family) << "\","
               << "\"canonical_type\":\"" << json_escape(report.canonical_type) << "\","
               << "\"is_alias\":" << std::boolalpha << report.is_alias << ','
               << "\"is_distinct\":false,"
               << "\"is_extension\":" << report.is_extension << ','
               << "\"special_boolean\":" << report.special_boolean << ','
               << "\"size_bytes\":" << report.size_bytes << ','
               << "\"alignment_bytes\":" << report.alignment_bytes << ','
               << "\"object_bits\":" << report.object_bits << ','
               << "\"value_bits\":" << report.value_bits << ','
               << "\"signed_oracle\":" << report.signed_oracle << ','
               << "\"unsigned_oracle\":" << report.unsigned_oracle << ','
               << "\"numeric_limits_signed\":" << report.numeric_limits_signed << ','
               << "\"observed_minus_one_is_negative\":"
               << report.observed_minus_one_is_negative << ','
               << "\"observed_zero_minus_one_is_negative\":"
               << report.observed_zero_minus_one_is_negative << ','
               << "\"observed_complement_zero_is_negative\":"
               << report.observed_complement_zero_is_negative << ','
               << "\"complement_bytes_all_ff\":" << report.complement_bytes_all_ff << ','
               << "\"arithmetic_result_same_as_input\":"
               << report.arithmetic_result_same_as_input << ','
               << "\"arithmetic_result_type\":\""
               << json_escape(report.arithmetic_result_type) << "\","
               << "\"integer_endian\":\"platform\","
               << "\"overflow_semantics\":\"" << overflow_semantics << "\","
               << "\"numeric_limits_is_modulo\":" << report.numeric_limits_is_modulo << ','
               << "\"minimum\":\"" << json_escape(report.minimum) << "\","
               << "\"maximum\":\"" << json_escape(report.maximum) << "\","
               << "\"zero_minus_one\":\"" << json_escape(report.zero_minus_one) << "\","
               << "\"complement_zero\":\"" << json_escape(report.complement_zero) << "\","
               << "\"maximum_plus_one\":\"" << json_escape(report.maximum_plus_one) << "\","
               << "\"minimum_minus_one\":\"" << json_escape(report.minimum_minus_one) << "\","
               << "\"bytes_zero\":\"" << json_escape(report.bytes_zero) << "\","
               << "\"bytes_one\":\"" << json_escape(report.bytes_one) << "\","
               << "\"bytes_minus_one\":\"" << json_escape(report.bytes_minus_one) << "\","
               << "\"bytes_minimum\":\"" << json_escape(report.bytes_minimum) << "\","
               << "\"bytes_maximum\":\"" << json_escape(report.bytes_maximum) << "\","
               << "\"checked_add_overflow\":" << report.checked_add_overflow << ','
               << "\"checked_subtract_overflow\":" << report.checked_subtract_overflow << ','
               << "\"direct_boundary_overflow_executed\":"
               << report.direct_boundary_overflow_executed << ','
               << "\"direct_signed_overflow_executed\":"
               << report.direct_signed_overflow_executed << ','
               << "\"underflow_not_saturate\":" << report.underflow_not_saturate << ','
               << "\"overflow_not_saturate\":" << report.overflow_not_saturate << ','
               << "\"discovery_path\":\"" << report.discovery.path << "\","
               << "\"discovery_conclusive\":" << report.discovery.conclusive << ','
               << "\"internally_consistent\":" << report.internally_consistent
               << "}\n";
        return;
    }

    output << report.label;
    if (report.is_alias) {
        output << " [alias]";
    }
    if (report.is_extension) {
        output << " [extension]";
    }
    if (report.special_boolean) {
        output << " [boolean]";
    }
    output << "\n"
           << "  family/canonical         : " << report.family << " / "
           << report.canonical_type << '\n'
           << "  size/alignment           : " << report.size_bytes << " / "
           << report.alignment_bytes << " bytes\n"
           << "  object/value bits        : " << report.object_bits << " / "
           << report.value_bits << '\n'
           << "  signed/unsigned traits   : " << std::boolalpha << report.signed_oracle
           << " / " << report.unsigned_oracle << '\n';

    if (report.special_boolean) {
        output << "  range                    : [false, true]\n"
               << "  bytes(false)             : " << report.bytes_zero << '\n'
               << "  bytes(true)              : " << report.bytes_one << '\n'
               << "  internally consistent    : " << report.internally_consistent << "\n\n";
        return;
    }

    output << "  discovered signed        : " << report.discovery.is_signed
           << " (" << report.discovery.path
           << ", conclusive=" << report.discovery.conclusive << ")\n"
           << "  observed -1 < 0          : " << report.observed_minus_one_is_negative << '\n'
           << "  observed (0 - 1) < 0     : "
           << report.observed_zero_minus_one_is_negative << '\n'
           << "  observed (~0) < 0        : "
           << report.observed_complement_zero_is_negative << '\n'
           << "  ~0 bytes all FF          : " << report.complement_bytes_all_ff << '\n'
           << "  arithmetic expression    : " << report.arithmetic_result_type
           << " (same as input: " << report.arithmetic_result_same_as_input << ")\n"
           << "  overflow semantics       : " << overflow_semantics << '\n'
           << "  range                    : [" << report.minimum << ", "
           << report.maximum << "]\n"
           << "  0 - 1                    : " << report.zero_minus_one << '\n'
           << "  ~0                       : " << report.complement_zero << '\n'
           << "  max + 1                  : " << report.maximum_plus_one << '\n'
           << "  min - 1                  : " << report.minimum_minus_one << '\n'
           << "  bytes(0)                 : " << report.bytes_zero << '\n'
           << "  bytes(1)                 : " << report.bytes_one << '\n'
           << "  bytes(-1)                : " << report.bytes_minus_one << '\n'
           << "  bytes(min)               : " << report.bytes_minimum << '\n'
           << "  bytes(max)               : " << report.bytes_maximum << '\n'
           << "  checked max+1 overflow   : " << report.checked_add_overflow << '\n'
           << "  checked min-1 overflow   : " << report.checked_subtract_overflow << '\n'
           << "  direct boundary overflow : "
           << report.direct_boundary_overflow_executed << '\n'
           << "  direct signed overflow   : "
           << report.direct_signed_overflow_executed << '\n'
           << "  internally consistent    : " << report.internally_consistent << "\n\n";
}

}  // namespace integer_semantics
