package main

import "base:intrinsics"
import "core:testing"

expect_integer_discovery :: proc(
	t: ^testing.T,
	expected_signed: bool,
	$T: typeid,
) where intrinsics.type_is_integer(T) {
	discovered, conclusive, _ := discover_integer_signed(T)
	testing.expect(t, conclusive, "signedness discovery must be conclusive")
	testing.expect_value(t, discovered, expected_signed)

	zero := T(0)
	one := T(1)
	maximum := max(T)
	minimum := min(T)
	maximum_plus_one := maximum + one
	minimum_minus_one := minimum - one
	checked_add_value, add_overflow := intrinsics.overflow_add(maximum, one)
	checked_subtract_value, subtract_overflow := intrinsics.overflow_sub(minimum, one)

	testing.expect(t, all_bytes_are_ff(~zero), "~0 must have all object bytes set")
	testing.expect_value(t, zero-one < zero, expected_signed)
	testing.expect_value(t, ~zero < zero, expected_signed)
	testing.expect(t, add_overflow, "max + 1 must report overflow")
	testing.expect(t, subtract_overflow, "min - 1 must report overflow")
	testing.expect_value(t, checked_add_value, maximum_plus_one)
	testing.expect_value(t, checked_subtract_value, minimum_minus_one)
}

@(test)
test_signed_catalog :: proc(t: ^testing.T) {
	expect_integer_discovery(t, true, i8)
	expect_integer_discovery(t, true, i16)
	expect_integer_discovery(t, true, i32)
	expect_integer_discovery(t, true, i64)
	expect_integer_discovery(t, true, i128)
	expect_integer_discovery(t, true, int)
}

@(test)
test_unsigned_catalog :: proc(t: ^testing.T) {
	expect_integer_discovery(t, false, u8)
	expect_integer_discovery(t, false, u16)
	expect_integer_discovery(t, false, u32)
	expect_integer_discovery(t, false, u64)
	expect_integer_discovery(t, false, u128)
	expect_integer_discovery(t, false, uint)
	expect_integer_discovery(t, false, uintptr)
}

@(test)
test_endian_specific_catalog :: proc(t: ^testing.T) {
	expect_integer_discovery(t, true, i16le)
	expect_integer_discovery(t, false, u16le)
	expect_integer_discovery(t, true, i16be)
	expect_integer_discovery(t, false, u16be)
}

@(test)
test_distinct_integer_catalog :: proc(t: ^testing.T) {
	expect_integer_discovery(t, true, Probe_Signed_Distinct)
	expect_integer_discovery(t, false, Probe_Unsigned_Distinct)
}
