"""Compare Odin and C++ integer-semantics JSONL reports."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class Report:
    path: Path
    metadata: dict[str, Any]
    rows: tuple[dict[str, Any], ...]
####


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("odin_report", type=Path)
    parser.add_argument("cpp_report", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()
####


def load_report(path: Path) -> Report:
    metadata: dict[str, Any] | None = None
    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            ####
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {error}") from error
            ####

            if record.get("record_kind") == "metadata":
                metadata = record
            elif record.get("record_kind") == "integer_type":
                rows.append(record)
            else:
                raise ValueError(
                    f"{path}:{line_number}: unsupported record_kind={record.get('record_kind')!r}"
                )
            ####
        ####
    ####

    if metadata is None:
        raise ValueError(f"{path}: missing metadata record")
    ####
    return Report(path=path, metadata=metadata, rows=tuple(rows))
####


def rows_by_label(report: Report) -> dict[str, dict[str, Any]]:
    return {str(row["label"]): row for row in report.rows}
####


def bool_text(value: object) -> str:
    return "yes" if bool(value) else "no"
####


def consistency_failures(report: Report) -> list[str]:
    return [
        str(row["label"])
        for row in report.rows
        if not bool(row.get("internally_consistent", False))
    ]
####


def markdown_table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    ####
    return "\n".join(lines)
####


def fixed_width_pairs(
    odin: Report,
    cpp: Report,
) -> list[tuple[object, ...]]:
    odin_rows = rows_by_label(odin)
    cpp_rows = rows_by_label(cpp)
    pairs = (
        ("i8", "std::int8_t"),
        ("u8", "std::uint8_t"),
        ("i16", "std::int16_t"),
        ("u16", "std::uint16_t"),
        ("i32", "std::int32_t"),
        ("u32", "std::uint32_t"),
        ("i64", "std::int64_t"),
        ("u64", "std::uint64_t"),
    )
    output: list[tuple[object, ...]] = []

    for odin_label, cpp_label in pairs:
        odin_row = odin_rows.get(odin_label)
        cpp_row = cpp_rows.get(cpp_label)
        if odin_row is None or cpp_row is None:
            output.append((odin_label, cpp_label, "missing", "—", "—", "—"))
            continue
        ####

        same_shape = (
            odin_row.get("object_bits") == cpp_row.get("object_bits")
            and odin_row.get("value_bits") == cpp_row.get("value_bits")
            and odin_row.get("signed_oracle") == cpp_row.get("signed_oracle")
        )
        output.append(
            (
                odin_label,
                cpp_label,
                "match" if same_shape else "different",
                odin_row.get("object_bits"),
                cpp_row.get("object_bits"),
                "signed" if odin_row.get("signed_oracle") else "unsigned",
            )
        )
    ####
    return output
####


def promotion_rows(report: Report) -> list[tuple[object, ...]]:
    rows: list[tuple[object, ...]] = []
    for row in report.rows:
        if bool(row.get("special_boolean")):
            continue
        ####
        if not bool(row.get("arithmetic_result_same_as_input", True)):
            rows.append(
                (
                    row.get("label"),
                    row.get("canonical_type"),
                    row.get("arithmetic_result_type"),
                )
            )
        ####
    ####
    return rows
####


def render_comparison(odin: Report, cpp: Report) -> str:
    odin_failures = consistency_failures(odin)
    cpp_failures = consistency_failures(cpp)
    odin_rows = rows_by_label(odin)
    cpp_rows = rows_by_label(cpp)

    lines = [
        "# Integer Semantics Comparison",
        "",
        "## Runs",
        "",
        (f"- Odin: `{odin.metadata.get('os')}/{odin.metadata.get('architecture')}`, "
         f"endian `{odin.metadata.get('native_endian')}`"),
        (f"- C++: `{cpp.metadata.get('compiler')} {cpp.metadata.get('compiler_version')}`, "
         f"`{cpp.metadata.get('os')}/{cpp.metadata.get('architecture')}`, "
         f"endian `{cpp.metadata.get('native_endian')}`"),
        "",
        "## Internal consistency",
        "",
        f"- Odin: {len(odin.rows)} rows; failures: "
        + (", ".join(odin_failures) if odin_failures else "none"),
        f"- C++: {len(cpp.rows)} rows; failures: "
        + (", ".join(cpp_failures) if cpp_failures else "none"),
        "",
        "## Fixed-width shape comparison",
        "",
        markdown_table(
            ("Odin", "C++", "Shape", "Odin bits", "C++ bits", "Signedness"),
            fixed_width_pairs(odin, cpp),
        ),
        "",
        "## Deliberate semantic differences",
        "",
    ]

    odin_i32 = odin_rows.get("i32", {})
    cpp_i32 = cpp_rows.get("std::int32_t", cpp_rows.get("int", {}))
    odin_bool = odin_rows.get("bool", {})
    cpp_bool = cpp_rows.get("bool", {})

    difference_rows: list[tuple[object, ...]] = [
        (
            "Signed max + 1",
            odin_i32.get("maximum_plus_one", "missing"),
            cpp_i32.get("maximum_plus_one", "missing"),
        ),
        (
            "Direct signed overflow executed",
            bool_text(odin_i32.get("direct_signed_overflow_executed")),
            bool_text(cpp_i32.get("direct_signed_overflow_executed")),
        ),
        (
            "bool classified unsigned",
            bool_text(odin_bool.get("unsigned_oracle")),
            bool_text(cpp_bool.get("unsigned_oracle")),
        ),
        (
            "Narrow arithmetic remains input type",
            bool_text(odin_rows.get("u8", {}).get("arithmetic_result_same_as_input")),
            bool_text(cpp_rows.get("unsigned char", {}).get("arithmetic_result_same_as_input")),
        ),
    ]
    lines.extend(
        [
            markdown_table(("Probe", "Odin", "C++"), difference_rows),
            "",
            "## C++ promotion observations",
            "",
        ]
    )

    promotions = promotion_rows(cpp)
    if promotions:
        lines.append(markdown_table(("Label", "Canonical", "Expression type"), promotions))
    else:
        lines.append("No integral promotions were observed in the selected C++ catalog.")
    ####
    lines.append("")

    return "\n".join(lines)
####


def main() -> int:
    arguments = parse_args()
    odin = load_report(arguments.odin_report)
    cpp = load_report(arguments.cpp_report)
    rendered = render_comparison(odin, cpp)

    if arguments.output is None:
        print(rendered)
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered + "\n", encoding="utf-8")
        print(arguments.output)
    ####

    return 1 if consistency_failures(odin) or consistency_failures(cpp) else 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
