package main

import "base:intrinsics"
import "core:fmt"

Output_Format :: enum {
	Text,
	JSONL,
}

Probe_Options :: struct {
	format:          Output_Format,
	include_aliases: bool,
	include_endian:  bool,
}

Probe_Signed_Distinct   :: distinct i32
Probe_Unsigned_Distinct :: distinct u32

all_bytes_are_ff :: proc(value: $T) -> bool {
	data := transmute([size_of(T)]byte)value
	for element in data {
		if element != 0xff {
			return false
		}
	}
	return true
}

print_bytes_hex :: proc(value: $T) {
	data := transmute([size_of(T)]byte)value
	fmt.print("\"")
	for element, index in data {
		if index != 0 {
			fmt.print(" ")
		}
		fmt.printf("%02X", element)
	}
	fmt.print("\"")
}

type_endian_name :: proc($T: typeid) -> string {
	when intrinsics.type_is_endian_platform(T) {
		return "platform"
	} else when intrinsics.type_is_endian_little(T) {
		return "little"
	} else when intrinsics.type_is_endian_big(T) {
		return "big"
	}
	return "unknown"
}

discover_integer_signed :: proc($T: typeid) -> (
	is_signed: bool,
	conclusive: bool,
	path: string,
) where intrinsics.type_is_integer(T) {
	zero := T(0)
	one := T(1)
	all_ones := ~zero

	if all_bytes_are_ff(all_ones) {
		return all_ones < zero, true, "bitwise-not"
	}

	underflow_value := zero - one
	if underflow_value != zero {
		return underflow_value < zero, true, "zero-minus-one"
	}

	maximum := max(T)
	overflow_value := maximum + one
	if overflow_value != maximum {
		// This proves non-saturating boundary behavior, but it cannot
		// distinguish signed from unsigned wrapping: both results may
		// compare less than maximum. Keep it as an observation only.
		return false, false, "maximum-plus-one-nondiscriminating"
	}

	return false, false, "inconclusive"
}

write_integer_json :: proc(
	label: string,
	family: string,
	canonical_type: string,
	is_alias: bool,
	is_distinct: bool,
	$T: typeid,
) where intrinsics.type_is_integer(T) {
	zero := T(0)
	one := T(1)
	minus_one := T(-1)
	minimum := min(T)
	maximum := max(T)
	zero_minus_one := zero - one
	complement_zero := ~zero
	maximum_plus_one := maximum + one
	minimum_minus_one := minimum - one
	checked_add_value, checked_add_overflow := intrinsics.overflow_add(maximum, one)
	checked_subtract_value, checked_subtract_overflow := intrinsics.overflow_sub(minimum, one)
	discovered_signed, discovery_conclusive, discovery_path := discover_integer_signed(T)
	signed_oracle := !intrinsics.type_is_unsigned(T)
	object_bits := 8 * size_of(T)
	value_bits := object_bits - (1 if signed_oracle else 0)
	arithmetic_result_same_as_input :: type_of(zero - one) == T
	complement_bytes_all_ff := all_bytes_are_ff(complement_zero)
	underflow_not_saturate := zero_minus_one != zero
	overflow_not_saturate := maximum_plus_one != maximum
	internally_consistent :=
		discovery_conclusive &&
		discovered_signed == signed_oracle &&
		(zero_minus_one < zero) == signed_oracle &&
		(complement_zero < zero) == signed_oracle &&
		complement_bytes_all_ff &&
		underflow_not_saturate &&
		overflow_not_saturate &&
		checked_add_overflow &&
		checked_subtract_overflow &&
		checked_add_value == maximum_plus_one &&
		checked_subtract_value == minimum_minus_one

	fmt.print("{")
	fmt.print("\"record_kind\":\"integer_type\",")
	fmt.print("\"language\":\"Odin\",")
	fmt.printf("\"label\":\"%s\",", label)
	fmt.printf("\"family\":\"%s\",", family)
	fmt.printf("\"canonical_type\":\"%s\",", canonical_type)
	fmt.printf("\"is_alias\":%v,", is_alias)
	fmt.printf("\"is_distinct\":%v,", is_distinct)
	fmt.print("\"is_extension\":false,")
	fmt.print("\"special_boolean\":false,")
	fmt.printf("\"size_bytes\":%d,", size_of(T))
	fmt.printf("\"alignment_bytes\":%d,", align_of(T))
	fmt.printf("\"object_bits\":%d,", object_bits)
	fmt.printf("\"value_bits\":%d,", value_bits)
	fmt.printf("\"signed_oracle\":%v,", signed_oracle)
	fmt.printf("\"unsigned_oracle\":%v,", intrinsics.type_is_unsigned(T))
	fmt.print("\"numeric_limits_signed\":null,")
	fmt.printf("\"observed_minus_one_is_negative\":%v,", minus_one < zero)
	fmt.printf("\"observed_zero_minus_one_is_negative\":%v,", zero_minus_one < zero)
	fmt.printf("\"observed_complement_zero_is_negative\":%v,", complement_zero < zero)
	fmt.printf("\"complement_bytes_all_ff\":%v,", complement_bytes_all_ff)
	fmt.printf("\"arithmetic_result_same_as_input\":%v,", arithmetic_result_same_as_input)
	fmt.printf("\"arithmetic_result_type\":\"%s\",", label if arithmetic_result_same_as_input else "different/unknown")
	fmt.printf("\"integer_endian\":\"%s\",", type_endian_name(T))
	fmt.print("\"overflow_semantics\":\"defined; result follows the signed or unsigned integer representation\",")
	fmt.print("\"numeric_limits_is_modulo\":null,")
	fmt.printf("\"minimum\":\"%v\",", minimum)
	fmt.printf("\"maximum\":\"%v\",", maximum)
	fmt.printf("\"zero_minus_one\":\"%v\",", zero_minus_one)
	fmt.printf("\"complement_zero\":\"%v\",", complement_zero)
	fmt.printf("\"maximum_plus_one\":\"%v\",", maximum_plus_one)
	fmt.printf("\"minimum_minus_one\":\"%v\",", minimum_minus_one)
	fmt.print("\"bytes_zero\":")
	print_bytes_hex(zero)
	fmt.print(",\"bytes_one\":")
	print_bytes_hex(one)
	fmt.print(",\"bytes_minus_one\":")
	print_bytes_hex(minus_one)
	fmt.print(",\"bytes_minimum\":")
	print_bytes_hex(minimum)
	fmt.print(",\"bytes_maximum\":")
	print_bytes_hex(maximum)
	fmt.printf(",\"checked_add_overflow\":%v", checked_add_overflow)
	fmt.printf(",\"checked_subtract_overflow\":%v", checked_subtract_overflow)
	fmt.print(",\"direct_boundary_overflow_executed\":true")
	fmt.printf(",\"direct_signed_overflow_executed\":%v", signed_oracle)
	fmt.printf(",\"underflow_not_saturate\":%v", underflow_not_saturate)
	fmt.printf(",\"overflow_not_saturate\":%v", overflow_not_saturate)
	fmt.printf(",\"discovery_path\":\"%s\"", discovery_path)
	fmt.printf(",\"discovery_conclusive\":%v", discovery_conclusive)
	fmt.printf(",\"internally_consistent\":%v", internally_consistent)
	fmt.println("}")
}

write_integer_text :: proc(
	label: string,
	family: string,
	canonical_type: string,
	is_alias: bool,
	is_distinct: bool,
	$T: typeid,
) where intrinsics.type_is_integer(T) {
	zero := T(0)
	one := T(1)
	minus_one := T(-1)
	minimum := min(T)
	maximum := max(T)
	zero_minus_one := zero - one
	complement_zero := ~zero
	maximum_plus_one := maximum + one
	minimum_minus_one := minimum - one
	checked_add_value, checked_add_overflow := intrinsics.overflow_add(maximum, one)
	checked_subtract_value, checked_subtract_overflow := intrinsics.overflow_sub(minimum, one)
	discovered_signed, discovery_conclusive, discovery_path := discover_integer_signed(T)
	signed_oracle := !intrinsics.type_is_unsigned(T)
	arithmetic_result_same_as_input :: type_of(zero - one) == T

	fmt.printf("%s", label)
	if is_alias {
		fmt.print(" [alias]")
	}
	if is_distinct {
		fmt.print(" [distinct]")
	}
	fmt.println()
	fmt.printf("  family/canonical         : %s / %s\n", family, canonical_type)
	fmt.printf("  size/alignment           : %d / %d bytes\n", size_of(T), align_of(T))
	fmt.printf("  object/value bits        : %d / %d\n", 8*size_of(T), 8*size_of(T) - (1 if signed_oracle else 0))
	fmt.printf("  integer endian           : %s\n", type_endian_name(T))
	fmt.printf("  signed oracle            : %v\n", signed_oracle)
	fmt.printf("  discovered signed        : %v (%s, conclusive=%v)\n", discovered_signed, discovery_path, discovery_conclusive)
	fmt.printf("  observed -1 < 0          : %v\n", minus_one < zero)
	fmt.printf("  observed (0 - 1) < 0     : %v\n", zero_minus_one < zero)
	fmt.printf("  observed (~0) < 0        : %v\n", complement_zero < zero)
	fmt.printf("  ~0 bytes all FF          : %v\n", all_bytes_are_ff(complement_zero))
	fmt.printf("  expression remains T     : %v\n", arithmetic_result_same_as_input)
	fmt.printf("  range                    : [%v, %v]\n", minimum, maximum)
	fmt.printf("  0 - 1                    : %v\n", zero_minus_one)
	fmt.printf("  ~0                       : %v\n", complement_zero)
	fmt.printf("  max + 1                  : %v\n", maximum_plus_one)
	fmt.printf("  min - 1                  : %v\n", minimum_minus_one)
	fmt.print("  bytes(0)                 : ")
	print_bytes_hex(zero)
	fmt.println()
	fmt.print("  bytes(1)                 : ")
	print_bytes_hex(one)
	fmt.println()
	fmt.print("  bytes(-1)                : ")
	print_bytes_hex(minus_one)
	fmt.println()
	fmt.print("  bytes(min)               : ")
	print_bytes_hex(minimum)
	fmt.println()
	fmt.print("  bytes(max)               : ")
	print_bytes_hex(maximum)
	fmt.println()
	fmt.printf("  checked max+1            : %v, overflow=%v\n", checked_add_value, checked_add_overflow)
	fmt.printf("  checked min-1            : %v, overflow=%v\n", checked_subtract_value, checked_subtract_overflow)
	fmt.println("  direct boundary overflow : executed; defined in Odin")
	fmt.printf("  direct signed overflow   : %v\n", signed_oracle)
	fmt.println()
}

probe_integer :: proc(
	options: Probe_Options,
	label: string,
	family: string,
	canonical_type: string,
	is_alias: bool,
	is_distinct: bool,
	$T: typeid,
) where intrinsics.type_is_integer(T) {
	switch options.format {
	case .JSONL:
		write_integer_json(label, family, canonical_type, is_alias, is_distinct, T)
	case .Text:
		write_integer_text(label, family, canonical_type, is_alias, is_distinct, T)
	}
}

probe_boolean :: proc(
	options: Probe_Options,
	label: string,
	$T: typeid,
) where intrinsics.type_is_boolean(T) {
	zero := T(false)
	one := T(true)
	internally_consistent := intrinsics.type_is_boolean(T) && !intrinsics.type_is_integer(T)

	if options.format == .JSONL {
		fmt.print("{")
		fmt.print("\"record_kind\":\"integer_type\",")
		fmt.print("\"language\":\"Odin\",")
		fmt.printf("\"label\":\"%s\",", label)
		fmt.print("\"family\":\"boolean type\",")
		fmt.printf("\"canonical_type\":\"%s\",", label)
		fmt.print("\"is_alias\":false,")
		fmt.print("\"is_distinct\":false,")
		fmt.print("\"is_extension\":false,")
		fmt.print("\"special_boolean\":true,")
		fmt.printf("\"size_bytes\":%d,", size_of(T))
		fmt.printf("\"alignment_bytes\":%d,", align_of(T))
		fmt.printf("\"object_bits\":%d,", 8*size_of(T))
		fmt.print("\"value_bits\":1,")
		fmt.print("\"signed_oracle\":false,")
		fmt.printf("\"unsigned_oracle\":%v,", intrinsics.type_is_unsigned(T))
		fmt.print("\"numeric_limits_signed\":null,")
		fmt.print("\"observed_minus_one_is_negative\":false,")
		fmt.print("\"observed_zero_minus_one_is_negative\":false,")
		fmt.print("\"observed_complement_zero_is_negative\":false,")
		fmt.print("\"complement_bytes_all_ff\":false,")
		fmt.print("\"arithmetic_result_same_as_input\":false,")
		fmt.print("\"arithmetic_result_type\":\"not applicable\",")
		fmt.print("\"integer_endian\":\"not applicable\",")
		fmt.print("\"overflow_semantics\":\"not applicable\",")
		fmt.print("\"numeric_limits_is_modulo\":null,")
		fmt.print("\"minimum\":\"false\",")
		fmt.print("\"maximum\":\"true\",")
		fmt.print("\"zero_minus_one\":\"not applicable\",")
		fmt.print("\"complement_zero\":\"not applicable\",")
		fmt.print("\"maximum_plus_one\":\"not applicable\",")
		fmt.print("\"minimum_minus_one\":\"not applicable\",")
		fmt.print("\"bytes_zero\":")
		print_bytes_hex(zero)
		fmt.print(",\"bytes_one\":")
		print_bytes_hex(one)
		fmt.print(",\"bytes_minus_one\":\"not applicable\"")
		fmt.print(",\"bytes_minimum\":")
		print_bytes_hex(zero)
		fmt.print(",\"bytes_maximum\":")
		print_bytes_hex(one)
		fmt.print(",\"checked_add_overflow\":false")
		fmt.print(",\"checked_subtract_overflow\":false")
		fmt.print(",\"direct_boundary_overflow_executed\":false")
		fmt.print(",\"direct_signed_overflow_executed\":false")
		fmt.print(",\"underflow_not_saturate\":false")
		fmt.print(",\"overflow_not_saturate\":false")
		fmt.print(",\"discovery_path\":\"not applicable\"")
		fmt.print(",\"discovery_conclusive\":false")
		fmt.printf(",\"internally_consistent\":%v", internally_consistent)
		fmt.println("}")
		return
	}

	fmt.printf("%s [boolean]\n", label)
	fmt.printf("  size/alignment           : %d / %d bytes\n", size_of(T), align_of(T))
	fmt.printf("  type_is_boolean          : %v\n", intrinsics.type_is_boolean(T))
	fmt.printf("  type_is_integer          : %v\n", intrinsics.type_is_integer(T))
	fmt.printf("  type_is_unsigned         : %v\n", intrinsics.type_is_unsigned(T))
	fmt.print("  bytes(false)             : ")
	print_bytes_hex(zero)
	fmt.println()
	fmt.print("  bytes(true)              : ")
	print_bytes_hex(one)
	fmt.println("\n")
}

probe_rune :: proc(options: Probe_Options) {
	zero := rune(0)
	one := rune(1)
	minus_one := rune(-1)
	minimum := min(rune)
	maximum := max(rune)
	zero_minus_one := zero - one
	complement_zero := ~zero
	maximum_plus_one := maximum + one
	minimum_minus_one := minimum - one
	checked_add_value_i32, checked_add_overflow := intrinsics.overflow_add(i32(maximum), i32(one))
	checked_subtract_value_i32, checked_subtract_overflow := intrinsics.overflow_sub(i32(minimum), i32(one))
	arithmetic_result_same_as_input :: type_of(zero - one) == rune
	internally_consistent :=
		intrinsics.type_is_rune(rune) &&
		!intrinsics.type_is_unsigned(rune) &&
		minus_one < zero &&
		zero_minus_one < zero &&
		complement_zero < zero &&
		all_bytes_are_ff(complement_zero) &&
		checked_add_overflow &&
		checked_subtract_overflow &&
		checked_add_value_i32 == i32(maximum_plus_one) &&
		checked_subtract_value_i32 == i32(minimum_minus_one)

	if options.format == .JSONL {
		fmt.print("{")
		fmt.print("\"record_kind\":\"integer_type\",")
		fmt.print("\"language\":\"Odin\",")
		fmt.print("\"label\":\"rune\",")
		fmt.print("\"family\":\"distinct Unicode code-point integer\",")
		fmt.print("\"canonical_type\":\"rune\",")
		fmt.print("\"is_alias\":false,")
		fmt.print("\"is_distinct\":true,")
		fmt.print("\"is_extension\":false,")
		fmt.print("\"special_boolean\":false,")
		fmt.printf("\"size_bytes\":%d,", size_of(rune))
		fmt.printf("\"alignment_bytes\":%d,", align_of(rune))
		fmt.printf("\"object_bits\":%d,", 8*size_of(rune))
		fmt.printf("\"value_bits\":%d,", 8*size_of(rune)-1)
		fmt.print("\"signed_oracle\":true,")
		fmt.print("\"unsigned_oracle\":false,")
		fmt.print("\"numeric_limits_signed\":null,")
		fmt.printf("\"observed_minus_one_is_negative\":%v,", minus_one < zero)
		fmt.printf("\"observed_zero_minus_one_is_negative\":%v,", zero_minus_one < zero)
		fmt.printf("\"observed_complement_zero_is_negative\":%v,", complement_zero < zero)
		fmt.printf("\"complement_bytes_all_ff\":%v,", all_bytes_are_ff(complement_zero))
		fmt.printf("\"arithmetic_result_same_as_input\":%v,", arithmetic_result_same_as_input)
		fmt.print("\"arithmetic_result_type\":\"rune\",")
		fmt.print("\"integer_endian\":\"platform\",")
		fmt.print("\"overflow_semantics\":\"defined; result follows the signed integer representation\",")
		fmt.print("\"numeric_limits_is_modulo\":null,")
		fmt.printf("\"minimum\":\"%v\",", i32(minimum))
		fmt.printf("\"maximum\":\"%v\",", i32(maximum))
		fmt.printf("\"zero_minus_one\":\"%v\",", i32(zero_minus_one))
		fmt.printf("\"complement_zero\":\"%v\",", i32(complement_zero))
		fmt.printf("\"maximum_plus_one\":\"%v\",", i32(maximum_plus_one))
		fmt.printf("\"minimum_minus_one\":\"%v\",", i32(minimum_minus_one))
		fmt.print("\"bytes_zero\":")
		print_bytes_hex(zero)
		fmt.print(",\"bytes_one\":")
		print_bytes_hex(one)
		fmt.print(",\"bytes_minus_one\":")
		print_bytes_hex(minus_one)
		fmt.print(",\"bytes_minimum\":")
		print_bytes_hex(minimum)
		fmt.print(",\"bytes_maximum\":")
		print_bytes_hex(maximum)
		fmt.printf(",\"checked_add_overflow\":%v", checked_add_overflow)
		fmt.printf(",\"checked_subtract_overflow\":%v", checked_subtract_overflow)
		fmt.print(",\"direct_boundary_overflow_executed\":true")
		fmt.print(",\"direct_signed_overflow_executed\":true")
		fmt.print(",\"underflow_not_saturate\":true")
		fmt.print(",\"overflow_not_saturate\":true")
		fmt.print(",\"discovery_path\":\"rune-backing-i32\"")
		fmt.print(",\"discovery_conclusive\":true")
		fmt.printf(",\"internally_consistent\":%v", internally_consistent)
		fmt.println("}")
		return
	}

	fmt.println("rune [distinct Unicode code-point integer]")
	fmt.printf("  size/alignment           : %d / %d bytes\n", size_of(rune), align_of(rune))
	fmt.printf("  type_is_rune             : %v\n", intrinsics.type_is_rune(rune))
	fmt.printf("  type_is_integer          : %v\n", intrinsics.type_is_integer(rune))
	fmt.printf("  signed semantics         : true\n")
	fmt.printf("  expression remains rune  : %v\n", arithmetic_result_same_as_input)
	fmt.printf("  range                    : [%v, %v]\n", i32(minimum), i32(maximum))
	fmt.printf("  max + 1                  : %v\n", i32(maximum_plus_one))
	fmt.printf("  min - 1                  : %v\n", i32(minimum_minus_one))
	fmt.print("  bytes(-1)                : ")
	print_bytes_hex(minus_one)
	fmt.println("\n")
}
