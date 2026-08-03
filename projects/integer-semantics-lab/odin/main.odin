package main

import "core:fmt"
import "core:os"

print_help :: proc() {
	fmt.println("Usage: odin run ./odin -- [--format=text|jsonl] [--catalog=core|all]")
	fmt.println()
	fmt.println("Inspects Odin boolean and integer semantics across the selected catalog.")
	fmt.println("The all catalog adds endian-specific integers, aliases, and distinct integers.")
}

parse_options :: proc() -> Probe_Options {
	options := Probe_Options{
		format = .Text,
	}

	for argument in os.args[1:] {
		switch argument {
		case "--format=text":
			options.format = .Text
		case "--format=jsonl":
			options.format = .JSONL
		case "--catalog=core":
			options.include_aliases = false
			options.include_endian = false
		case "--catalog=all", "--all":
			options.include_aliases = true
			options.include_endian = true
		case "--aliases":
			options.include_aliases = true
		case "--endian":
			options.include_endian = true
		case "--help", "-h":
			print_help()
			os.exit(0)
		case:
			fmt.eprintf("Unknown argument: %s\n", argument)
			os.exit(2)
		}
	}
	return options
}

write_metadata :: proc(format: Output_Format) {
	if format == .JSONL {
		fmt.print("{")
		fmt.print("\"record_kind\":\"metadata\",")
		fmt.print("\"schema_version\":1,")
		fmt.print("\"language\":\"Odin\",")
		fmt.printf("\"compiler_version\":\"%s\",", ODIN_VERSION)
		fmt.printf("\"compiler_hash\":\"%s\",", ODIN_VERSION_HASH)
		fmt.printf("\"os\":\"%s\",", ODIN_OS_STRING)
		fmt.printf("\"architecture\":\"%s\",", ODIN_ARCH_STRING)
		fmt.printf("\"native_endian\":\"%s\",", ODIN_ENDIAN_STRING)
		fmt.printf("\"build_mode\":\"%v\",", ODIN_BUILD_MODE)
		fmt.printf("\"optimization\":\"%v\",", ODIN_OPTIMIZATION_MODE)
		fmt.printf("\"debug\":%v,", ODIN_DEBUG)
		fmt.printf("\"sanitizers\":\"%v\"", ODIN_SANITIZER_FLAGS)
		fmt.println("}")
		return
	}

	fmt.println("Integer Semantics Probe — Odin")
	fmt.printf("  compiler       : %s (%s)\n", ODIN_VERSION, ODIN_VERSION_HASH)
	fmt.printf("  target         : %s/%s\n", ODIN_OS_STRING, ODIN_ARCH_STRING)
	fmt.printf("  native endian  : %s\n", ODIN_ENDIAN_STRING)
	fmt.printf("  build mode     : %v\n", ODIN_BUILD_MODE)
	fmt.printf("  optimization   : %v\n", ODIN_OPTIMIZATION_MODE)
	fmt.printf("  sanitizers     : %v\n\n", ODIN_SANITIZER_FLAGS)
}

main :: proc() {
	options := parse_options()
	write_metadata(options.format)
	run_core_catalog(options)

	if options.include_endian {
		run_endian_catalog(options)
	}
	if options.include_aliases {
		run_alias_catalog(options)
	}
}
