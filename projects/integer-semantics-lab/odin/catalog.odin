package main

run_core_catalog :: proc(options: Probe_Options) {
	probe_boolean(options, "bool", bool)
	probe_boolean(options, "b8", b8)
	probe_boolean(options, "b16", b16)
	probe_boolean(options, "b32", b32)
	probe_boolean(options, "b64", b64)

	probe_rune(options)

	probe_integer(options, "i8", "fixed-width signed integer", "i8", false, false, i8)
	probe_integer(options, "u8", "fixed-width unsigned integer", "u8", false, false, u8)
	probe_integer(options, "i16", "fixed-width signed integer", "i16", false, false, i16)
	probe_integer(options, "u16", "fixed-width unsigned integer", "u16", false, false, u16)
	probe_integer(options, "i32", "fixed-width signed integer", "i32", false, false, i32)
	probe_integer(options, "u32", "fixed-width unsigned integer", "u32", false, false, u32)
	probe_integer(options, "i64", "fixed-width signed integer", "i64", false, false, i64)
	probe_integer(options, "u64", "fixed-width unsigned integer", "u64", false, false, u64)
	probe_integer(options, "i128", "fixed-width signed integer", "i128", false, false, i128)
	probe_integer(options, "u128", "fixed-width unsigned integer", "u128", false, false, u128)

	probe_integer(options, "int", "natural signed integer", "int", false, false, int)
	probe_integer(options, "uint", "natural unsigned integer", "uint", false, false, uint)
	probe_integer(options, "uintptr", "pointer-sized unsigned integer", "uintptr", false, false, uintptr)
}

run_endian_catalog :: proc(options: Probe_Options) {
	probe_integer(options, "i16le", "little-endian signed integer", "i16le", false, false, i16le)
	probe_integer(options, "u16le", "little-endian unsigned integer", "u16le", false, false, u16le)
	probe_integer(options, "i32le", "little-endian signed integer", "i32le", false, false, i32le)
	probe_integer(options, "u32le", "little-endian unsigned integer", "u32le", false, false, u32le)
	probe_integer(options, "i64le", "little-endian signed integer", "i64le", false, false, i64le)
	probe_integer(options, "u64le", "little-endian unsigned integer", "u64le", false, false, u64le)
	probe_integer(options, "i128le", "little-endian signed integer", "i128le", false, false, i128le)
	probe_integer(options, "u128le", "little-endian unsigned integer", "u128le", false, false, u128le)

	probe_integer(options, "i16be", "big-endian signed integer", "i16be", false, false, i16be)
	probe_integer(options, "u16be", "big-endian unsigned integer", "u16be", false, false, u16be)
	probe_integer(options, "i32be", "big-endian signed integer", "i32be", false, false, i32be)
	probe_integer(options, "u32be", "big-endian unsigned integer", "u32be", false, false, u32be)
	probe_integer(options, "i64be", "big-endian signed integer", "i64be", false, false, i64be)
	probe_integer(options, "u64be", "big-endian unsigned integer", "u64be", false, false, u64be)
	probe_integer(options, "i128be", "big-endian signed integer", "i128be", false, false, i128be)
	probe_integer(options, "u128be", "big-endian unsigned integer", "u128be", false, false, u128be)
}

run_alias_catalog :: proc(options: Probe_Options) {
	probe_integer(options, "byte", "builtin alias", "u8", true, false, byte)
	probe_integer(options, "Probe_Signed_Distinct", "user-defined distinct integer", "i32", false, true, Probe_Signed_Distinct)
	probe_integer(options, "Probe_Unsigned_Distinct", "user-defined distinct integer", "u32", false, true, Probe_Unsigned_Distinct)
}
