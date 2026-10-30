#!/usr/bin/env python3
"""Serve the local GLSL gallery and discover note and project shaders."""

from __future__ import annotations

import argparse
import io
import json
import os
import stat
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKIP_PARTS = {".git", ".venv", ".uv-cache", ".pytest_cache", "artifacts", "inbox"}
GALLERY_DIRECTORY = "projects/shaders/shader-gallery"
GALLERY_FILES = {
    f"{GALLERY_DIRECTORY}/index.html",
    f"{GALLERY_DIRECTORY}/shader-gallery.css",
    f"{GALLERY_DIRECTORY}/shader-gallery.js",
    "projects/shaders/README.md",
    "projects/README.md",
}


def supports_secure_open() -> bool:
    """Report whether this Python can open each component without following links."""
    return (
        os.open in os.supports_dir_fd
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "O_NONBLOCK")
    )
####


def _open_safe_file(repository_root: Path, relative: Path):
    """Open a regular allowlisted file without following path-component links."""
    if not relative.parts or any(part in SKIP_PARTS or part.startswith(".") for part in relative.parts):
        return None
    ####
    # Without descriptor-relative, no-follow opens, a path can be swapped
    # between validation and opening. Refuse file access rather than race.
    if not supports_secure_open():
        return None
    ####
    directory_fd = None
    file_fd = None
    try:
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        directory_fd = os.open(repository_root.resolve(), directory_flags)
        for part in relative.parts[:-1]:
            next_fd = os.open(part, directory_flags, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        ####
        file_fd = os.open(
            relative.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd
        )
        info = os.fstat(file_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            return None
        ####
        stream = os.fdopen(file_fd, "rb")
        file_fd = None
        return stream
    except (OSError, RuntimeError, ValueError):
        return None
    finally:
        if file_fd is not None:
            os.close(file_fd)
        ####
        if directory_fd is not None:
            os.close(directory_fd)
        ####
    ####
####


def _is_shader_path(relative: Path) -> bool:
    return relative.suffix == ".glsl" and (
        relative.parts[:1] == ("notes",)
        or relative.parts[:2] == ("projects", "shaders")
    )
####


def shader_catalog(repository_root: Path) -> list[dict[str, str]]:
    """Return every durable GLSL source file as browser-friendly metadata."""

    shader_roots = (repository_root / "notes", repository_root / "projects" / "shaders")
    shaders = []
    for path in sorted(path for root in shader_roots for path in root.rglob("*.glsl")):
        relative = path.relative_to(repository_root)
        if not _is_shader_path(relative):
            continue
        ####
        stream = _open_safe_file(repository_root, relative)
        if stream is None:
            continue
        ####
        stream.close()
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
    """Check known ignored components; this alone does not authorize a request."""

    request_path = unquote(urlsplit(request_target).path).lstrip("/")
    return any(part in SKIP_PARTS for part in Path(request_path).parts)
####


def _allowed_file(repository_root: Path, request_target: str) -> str | None:
    """Return an allowed relative file, never a directory listing."""
    try:
        request_path = unquote(urlsplit(request_target).path, errors="strict")
    except UnicodeError:
        return None
    ####
    if not request_path.startswith("/") or "\\" in request_path or "\x00" in request_path:
        return None
    ####
    raw_parts = request_path.lstrip("/").split("/")
    if any(part in {".", ".."} for part in raw_parts):
        return None
    ####
    relative = "/".join(raw_parts)
    if relative == GALLERY_DIRECTORY + "/":
        relative += "index.html"
    ####
    path = Path(relative)
    if relative not in GALLERY_FILES and not _is_shader_path(path):
        return None
    ####
    return relative
####


def handler_for(repository_root: Path):
    class GalleryHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(repository_root), **kwargs)
        ####

        def send_head(self):
            request_path = urlsplit(self.path).path
            if request_path == "/__shader_gallery__/shaders":
                payload = json.dumps(shader_catalog(repository_root), indent=2).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                return io.BytesIO(payload)
            ####
            if request_path == "/" + GALLERY_DIRECTORY:
                index = _allowed_file(repository_root, request_path + "/")
                stream = _open_safe_file(repository_root, Path(index)) if index is not None else None
                if stream is None:
                    self.send_error(404, "Gallery index is not available.")
                    return None
                ####
                stream.close()
                target = request_path + "/"
                query = urlsplit(self.path).query
                if query:
                    target += "?" + query
                ####
                self.send_response(301)
                self.send_header("Location", target)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            ####
            allowed = _allowed_file(repository_root, self.path)
            if allowed is None:
                self.send_error(404, "Only gallery assets and shader sources are served.")
                return None
            ####
            stream = _open_safe_file(repository_root, Path(allowed))
            if stream is None:
                self.send_error(404, "Gallery asset is unavailable.")
                return None
            ####
            info = os.fstat(stream.fileno())
            self.send_response(200)
            self.send_header("Content-Type", self.guess_type(allowed))
            self.send_header("Content-Length", str(info.st_size))
            self.send_header("Last-Modified", self.date_time_string(info.st_mtime))
            self.end_headers()
            return stream
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

    if not supports_secure_open():
        parser.exit(2, "shader gallery requires descriptor-relative no-follow file opens on this platform\n")
    ####
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
