#include "integer_semantics/probe.hpp"

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string_view>

namespace {

using integer_semantics::output_format;

struct command_line {
    output_format format{output_format::text};
    bool include_aliases{false};
    bool include_extensions{false};
};

[[nodiscard]] auto parse_command_line(const int argc, char** argv) -> command_line {
    command_line options{};

    for (int index = 1; index < argc; ++index) {
        const std::string_view argument{argv[index]};
        if (argument == "--format=jsonl") {
            options.format = output_format::jsonl;
        } else if (argument == "--format=text") {
            options.format = output_format::text;
        } else if (argument == "--aliases") {
            options.include_aliases = true;
        } else if (argument == "--extensions") {
            options.include_extensions = true;
        } else if (argument == "--catalog=all") {
            options.include_aliases = true;
            options.include_extensions = true;
        } else if (argument == "--catalog=core") {
            options.include_aliases = false;
            options.include_extensions = false;
        } else if (argument == "--help" || argument == "-h") {
            std::cout
                << "Usage: cpp_integer_semantics [--format=text|jsonl] "
                   "[--catalog=core|all] [--aliases] [--extensions]\n\n"
                << "Inspects the standard C++ integer and character type families.\n"
                << "--aliases adds fixed-, least-, fast-, pointer-, and library aliases.\n"
                << "--extensions adds compiler integer extensions when supported.\n";
            std::exit(0);
        } else {
            std::cerr << "Unknown argument: " << argument << '\n';
            std::exit(2);
        }
    }
    return options;
}

template <integer_semantics::cpp_integral T>
void emit(
    std::ostream& output,
    const output_format format,
    const std::string_view label,
    const std::string_view family,
    const bool is_alias,
    const bool is_extension,
    int& inconsistent_rows
) {
    const auto report = integer_semantics::inspect_type<T>(
        label,
        family,
        is_alias,
        is_extension
    );
    integer_semantics::write_report(output, report, format);
    if (!report.internally_consistent) {
        ++inconsistent_rows;
    }
}

void emit_core_catalog(
    std::ostream& output,
    const output_format format,
    int& inconsistent_rows
) {
    emit<bool>(output, format, "bool", "boolean integral type", false, false, inconsistent_rows);

    emit<char>(output, format, "char", "ordinary character type", false, false, inconsistent_rows);
    emit<signed char>(output, format, "signed char", "standard signed integer", false, false, inconsistent_rows);
    emit<unsigned char>(output, format, "unsigned char", "standard unsigned integer", false, false, inconsistent_rows);
    emit<wchar_t>(output, format, "wchar_t", "wide character type", false, false, inconsistent_rows);
    emit<char8_t>(output, format, "char8_t", "UTF-8 character type", false, false, inconsistent_rows);
    emit<char16_t>(output, format, "char16_t", "UTF-16 character type", false, false, inconsistent_rows);
    emit<char32_t>(output, format, "char32_t", "UTF-32 character type", false, false, inconsistent_rows);

    emit<short>(output, format, "short", "standard signed integer", false, false, inconsistent_rows);
    emit<unsigned short>(output, format, "unsigned short", "standard unsigned integer", false, false, inconsistent_rows);
    emit<int>(output, format, "int", "standard signed integer", false, false, inconsistent_rows);
    emit<unsigned int>(output, format, "unsigned int", "standard unsigned integer", false, false, inconsistent_rows);
    emit<long>(output, format, "long", "standard signed integer", false, false, inconsistent_rows);
    emit<unsigned long>(output, format, "unsigned long", "standard unsigned integer", false, false, inconsistent_rows);
    emit<long long>(output, format, "long long", "standard signed integer", false, false, inconsistent_rows);
    emit<unsigned long long>(output, format, "unsigned long long", "standard unsigned integer", false, false, inconsistent_rows);
}

void emit_alias_catalog(
    std::ostream& output,
    const output_format format,
    int& inconsistent_rows
) {
#ifdef INT8_MAX
    emit<std::int8_t>(output, format, "std::int8_t", "exact-width alias", true, false, inconsistent_rows);
    emit<std::uint8_t>(output, format, "std::uint8_t", "exact-width alias", true, false, inconsistent_rows);
#endif
#ifdef INT16_MAX
    emit<std::int16_t>(output, format, "std::int16_t", "exact-width alias", true, false, inconsistent_rows);
    emit<std::uint16_t>(output, format, "std::uint16_t", "exact-width alias", true, false, inconsistent_rows);
#endif
#ifdef INT32_MAX
    emit<std::int32_t>(output, format, "std::int32_t", "exact-width alias", true, false, inconsistent_rows);
    emit<std::uint32_t>(output, format, "std::uint32_t", "exact-width alias", true, false, inconsistent_rows);
#endif
#ifdef INT64_MAX
    emit<std::int64_t>(output, format, "std::int64_t", "exact-width alias", true, false, inconsistent_rows);
    emit<std::uint64_t>(output, format, "std::uint64_t", "exact-width alias", true, false, inconsistent_rows);
#endif

#define EMIT_WIDTH_ALIASES(bits) \
    emit<std::int_least##bits##_t>(output, format, "std::int_least" #bits "_t", "least-width alias", true, false, inconsistent_rows); \
    emit<std::uint_least##bits##_t>(output, format, "std::uint_least" #bits "_t", "least-width alias", true, false, inconsistent_rows); \
    emit<std::int_fast##bits##_t>(output, format, "std::int_fast" #bits "_t", "fast-width alias", true, false, inconsistent_rows); \
    emit<std::uint_fast##bits##_t>(output, format, "std::uint_fast" #bits "_t", "fast-width alias", true, false, inconsistent_rows)

    EMIT_WIDTH_ALIASES(8);
    EMIT_WIDTH_ALIASES(16);
    EMIT_WIDTH_ALIASES(32);
    EMIT_WIDTH_ALIASES(64);
#undef EMIT_WIDTH_ALIASES

#ifdef INTPTR_MAX
    emit<std::intptr_t>(output, format, "std::intptr_t", "pointer-capable alias", true, false, inconsistent_rows);
    emit<std::uintptr_t>(output, format, "std::uintptr_t", "pointer-capable alias", true, false, inconsistent_rows);
#endif
    emit<std::intmax_t>(output, format, "std::intmax_t", "maximum-width alias", true, false, inconsistent_rows);
    emit<std::uintmax_t>(output, format, "std::uintmax_t", "maximum-width alias", true, false, inconsistent_rows);
    emit<std::size_t>(output, format, "std::size_t", "library size alias", true, false, inconsistent_rows);
    emit<std::ptrdiff_t>(output, format, "std::ptrdiff_t", "library difference alias", true, false, inconsistent_rows);
}

void emit_extension_catalog(
    std::ostream& output,
    const output_format format,
    int& inconsistent_rows
) {
#if defined(__SIZEOF_INT128__)
    emit<__int128_t>(output, format, "__int128_t", "compiler signed integer extension", false, true, inconsistent_rows);
    emit<__uint128_t>(output, format, "__uint128_t", "compiler unsigned integer extension", false, true, inconsistent_rows);
#else
    (void)output;
    (void)format;
    (void)inconsistent_rows;
#endif
}

}  // namespace

int main(const int argc, char** argv) {
    const command_line options = parse_command_line(argc, argv);
    int inconsistent_rows = 0;

    integer_semantics::write_metadata(std::cout, options.format);
    emit_core_catalog(std::cout, options.format, inconsistent_rows);
    if (options.include_aliases) {
        emit_alias_catalog(std::cout, options.format, inconsistent_rows);
    }
    if (options.include_extensions) {
        emit_extension_catalog(std::cout, options.format, inconsistent_rows);
    }

    if (inconsistent_rows != 0) {
        std::cerr << "Detected " << inconsistent_rows << " internally inconsistent row(s).\n";
        return 1;
    }
    return 0;
}
