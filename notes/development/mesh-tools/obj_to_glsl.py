"""Convert the validated subset of an OBJ mesh to GLSL declarations."""

from __future__ import annotations

import argparse
from pathlib import Path

from obj_io import load_obj, to_glsl


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    rendered = to_glsl(load_obj(args.input))
    if args.output is None:
        print(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
