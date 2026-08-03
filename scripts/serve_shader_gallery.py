#!/usr/bin/env python3
"""Serve the local GLSL gallery and discover shaders under notes/."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".venv", ".uv-cache", ".pytest_cache", "artifacts", "inbox"}


def shader_catalog(repository_root: Path) -> list[dict[str, str]]:
    """Return every durable GLSL source file as browser-friendly metadata."""

    notes_root = repository_root / "notes"
    shaders = []
    for path in sorted(notes_root.rglob("*.glsl")):
        relative = path.relative_to(repository_root)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        ####
        relative_url = "/" + "/".join(quote(part) for part in relative.parts)
        shaders.append(
            {
                "path": relative.as_posix(),
                "url": relative_url,
                "name": path.stem,
            }
        )
    ####
    return shaders
####


def is_blocked_request(request_target: str) -> bool:
    """Keep the local gallery from serving ignored scratch or generated directories."""

    request_path = unquote(urlsplit(request_target).path).lstrip("/")
    return any(part in SKIP_PARTS for part in Path(request_path).parts)
####


def handler_for(repository_root: Path):
    class GalleryHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(repository_root), **kwargs)
        ####

        def do_GET(self) -> None:
            request_path = urlsplit(self.path).path
            if request_path == "/__shader_gallery__/shaders":
                payload = json.dumps(shader_catalog(repository_root), indent=2).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            ####
            if is_blocked_request(self.path):
                self.send_error(404, "Ignored repository content is not served by the gallery.")
                return
            ####
            super().do_GET()
        ####

        def log_message(self, format_string: str, *args) -> None:
            print(f"[shader-gallery] {format_string % args}")
        ####
    ####

    return GalleryHandler
####


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    arguments = parser.parse_args()

    server = ThreadingHTTPServer(
        (arguments.host, arguments.port), handler_for(REPOSITORY_ROOT)
    )
    print(
        "Shader gallery available at "
        f"http://{arguments.host}:{arguments.port}/projects/shaders/shader-gallery/"
    )
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping shader gallery.")
    finally:
        server.server_close()
    ####
    return 0
####


if __name__ == "__main__":
    raise SystemExit(main())
####
