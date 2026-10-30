from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

LAB_ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
####


compare_reports = load_module(
    "compare_reports_under_test",
    LAB_ROOT / "scripts" / "compare_reports.py",
)
run_lab = load_module("run_lab_under_test", LAB_ROOT / "scripts" / "run_lab.py")


def write_report(path: Path, metadata: dict, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(record) for record in [metadata, *rows]) + "\n",
        encoding="utf-8",
    )
####


def test_report_loading_and_helpers(tmp_path: Path) -> None:
    path = tmp_path / "report.jsonl"
    write_report(
        path,
        {"record_kind": "metadata", "os": "test"},
        [
            {"record_kind": "integer_type", "label": "i8", "internally_consistent": True},
            {"record_kind": "integer_type", "label": "bad", "internally_consistent": False},
        ],
    )

    report = compare_reports.load_report(path)

    assert report.path == path
    assert compare_reports.rows_by_label(report)["i8"]["label"] == "i8"
    assert compare_reports.bool_text(1) == "yes"
    assert compare_reports.bool_text(0) == "no"
    assert compare_reports.consistency_failures(report) == ["bad"]
    assert compare_reports.markdown_table(("A", "B"), [(1, "two")]) == (
        "| A | B |\n| --- | --- |\n| 1 | two |"
    )
####


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ('{"record_kind":"integer_type","label":"i8"}\n', "missing metadata"),
        ('{"record_kind":"metadata"}\nnot json\n', "invalid JSON"),
        ('{"record_kind":"metadata"}\n{"record_kind":"other"}\n', "unsupported record_kind"),
    ],
)
def test_report_loading_rejects_invalid_records(
    tmp_path: Path,
    contents: str,
    message: str,
) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        compare_reports.load_report(path)
    ####
####


def test_shape_and_promotion_comparisons() -> None:
    odin = compare_reports.Report(
        Path("odin.jsonl"),
        {"os": "linux", "architecture": "x64", "native_endian": "little"},
        (
            {"record_kind": "integer_type", "label": "i8", "object_bits": 8, "value_bits": 7, "signed_oracle": True},
            {"record_kind": "integer_type", "label": "i32", "maximum_plus_one": "wrapped", "direct_signed_overflow_executed": False},
            {"record_kind": "integer_type", "label": "bool", "unsigned_oracle": False},
            {"record_kind": "integer_type", "label": "u8", "arithmetic_result_same_as_input": True},
        ),
    )
    cpp = compare_reports.Report(
        Path("cpp.jsonl"),
        {"compiler": "clang", "compiler_version": "1", "os": "windows", "architecture": "x64", "native_endian": "little"},
        (
            {"record_kind": "integer_type", "label": "std::int8_t", "object_bits": 8, "value_bits": 6, "signed_oracle": True},
            {"record_kind": "integer_type", "label": "std::int32_t", "maximum_plus_one": "undefined", "direct_signed_overflow_executed": True},
            {"record_kind": "integer_type", "label": "bool", "unsigned_oracle": True, "special_boolean": True},
            {"record_kind": "integer_type", "label": "unsigned char", "arithmetic_result_same_as_input": False, "canonical_type": "unsigned char", "arithmetic_result_type": "int"},
        ),
    )

    pairs = compare_reports.fixed_width_pairs(odin, cpp)
    assert pairs[0] == ("i8", "std::int8_t", "different", 8, 8, "signed")
    assert pairs[1][2] == "missing"
    assert compare_reports.promotion_rows(cpp) == [("unsigned char", "unsigned char", "int")]

    rendered = compare_reports.render_comparison(odin, cpp)
    assert "# Integer Semantics Comparison" in rendered
    assert "undefined" in rendered
    assert "unsigned char" in rendered

    empty = compare_reports.Report(Path("empty"), {}, ())
    assert "No integral promotions" in compare_reports.render_comparison(empty, empty)
####


def test_compare_reports_main_writes_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    odin_path = tmp_path / "odin.jsonl"
    cpp_path = tmp_path / "cpp.jsonl"
    output_path = tmp_path / "nested" / "comparison.md"
    metadata = {"record_kind": "metadata"}
    write_report(odin_path, metadata, [])
    write_report(cpp_path, metadata, [])
    monkeypatch.setattr(
        sys,
        "argv",
        ["compare_reports.py", str(odin_path), str(cpp_path), "--output", str(output_path)],
    )

    assert compare_reports.main() == 0
    assert output_path.read_text(encoding="utf-8").startswith("# Integer Semantics Comparison")
####


def test_run_lab_helpers_and_orchestration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(run_lab.shutil, "which", lambda name: "tool" if name == "cmake" else None)
    calls: list[tuple[list[str], Path | None, Path | None]] = []

    def fake_run(command, *, cwd=None, stdout=None):
        calls.append((list(command), cwd, stdout))
    ####

    monkeypatch.setattr(run_lab, "run", fake_run)
    monkeypatch.setattr(run_lab, "REPORTS", tmp_path / "reports")
    build_dir = tmp_path / "build"
    configured_executable = build_dir / "Release" / "cpp_integer_semantics.exe"
    configured_executable.parent.mkdir(parents=True)
    configured_executable.write_text("stub", encoding="utf-8")

    assert run_lab.executable_path(build_dir, "cpp_integer_semantics", "Release") == configured_executable
    assert run_lab.run_cpp(build_dir, "Release").name == "cpp.jsonl"
    assert len(calls) == 4

    calls.clear()
    monkeypatch.setattr(run_lab.shutil, "which", lambda name: "odin" if name == "odin" else None)
    assert run_lab.run_odin().name == "odin.jsonl"
    assert len(calls) == 2

    monkeypatch.setattr(run_lab.shutil, "which", lambda _name: None)
    with pytest.raises(RuntimeError, match="cmake"):
        run_lab.run_cpp(build_dir, "Release")
    ####
    with pytest.raises(RuntimeError, match="odin"):
        run_lab.run_odin()
    ####
####


def test_run_lab_main_can_skip_all_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(run_lab, "REPORTS", tmp_path / "reports")
    monkeypatch.setattr(sys, "argv", ["run_lab.py", "--skip-cpp", "--skip-odin"])

    assert run_lab.main() == 0
    assert (tmp_path / "reports").is_dir()
####
