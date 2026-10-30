"""Exercise the gallery's HTTP handler with fake files and in-memory requests."""

from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import serve_shader_gallery
from scripts.serve_shader_gallery import (
    handler_for,
    shader_catalog,
    supports_secure_open,
)


class MemoryRequest:
    def __init__(self, method: str, path: str) -> None:
        self.reader = io.BytesIO(f"{method} {path} HTTP/1.0\r\nHost: localhost\r\n\r\n".encode())
        self.output = bytearray()
    ####

    def makefile(self, mode: str, *args, **kwargs):
        assert mode == "rb"
        return self.reader
    ####

    def sendall(self, data: bytes) -> None:
        self.output.extend(data)
    ####
####


def request(root: Path, method: str, path: str) -> tuple[int, dict[str, str], bytes]:
    connection = MemoryRequest(method, path)
    server = SimpleNamespace(server_name="localhost", server_port=80)
    handler_for(root)(connection, ("127.0.0.1", 1234), server)
    headers, _, body = bytes(connection.output).partition(b"\r\n\r\n")
    lines = headers.decode("iso-8859-1").split("\r\n")
    status = int(lines[0].split()[1])
    fields = dict(line.split(": ", 1) for line in lines[1:])
    return status, fields, body
####


@pytest.fixture
def fake_gallery(tmp_path: Path) -> Path:
    files = {
        ".env": "fake-secret",
        ".git/config": "fake-config",
        ".git/private.glsl": "fake-private-shader",
        "notes/aerospace/visible.glsl": "visible-note-shader",
        "projects/shaders/visible.glsl": "visible-project-shader",
        "projects/shaders/shader-gallery/index.html": "gallery-index",
        "projects/shaders/shader-gallery/shader-gallery.css": "gallery-style",
        "projects/shaders/shader-gallery/shader-gallery.js": "gallery-script",
        "projects/shaders/README.md": "shader-docs",
        "projects/README.md": "project-docs",
        "notes/aerospace/private.txt": "fake-private-file",
        "notes/.hidden.glsl": "fake-hidden-shader",
        "projects/shaders/artifacts/generated.glsl": "fake-generated",
    }
    for name, value in files.items():
        file = tmp_path / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(value, encoding="utf-8")
    ####
    return tmp_path
####


@pytest.mark.parametrize("method", ["GET", "HEAD"])
@pytest.mark.skipif(not supports_secure_open(), reason="secure descriptor-relative opens unavailable")
def test_only_gallery_assets_and_shader_sources_are_served(fake_gallery: Path, method: str) -> None:
    allowed = {
        "/projects/shaders/shader-gallery/": b"gallery-index",
        "/projects/shaders/shader-gallery/index.html": b"gallery-index",
        "/projects/shaders/shader-gallery/shader-gallery.css": b"gallery-style",
        "/projects/shaders/shader-gallery/shader-gallery.js": b"gallery-script",
        "/projects/shaders/README.md": b"shader-docs",
        "/projects/README.md": b"project-docs",
        "/notes/aerospace/visible.glsl": b"visible-note-shader",
        "/projects/shaders/visible.glsl": b"visible-project-shader",
    }
    for path, expected in allowed.items():
        status, _, body = request(fake_gallery, method, path)
        assert status == 200, path
        assert body == (expected if method == "GET" else b"")
    ####
    status, headers, body = request(fake_gallery, method, "/projects/shaders/shader-gallery")
    assert status == 301 and headers["Location"] == "/projects/shaders/shader-gallery/"
    assert body == b""
####


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_private_files_traversal_and_directory_listings_are_denied(fake_gallery: Path, method: str) -> None:
    denied = (
        "/.env", "/.git/config", "/", "/notes/", "/notes/aerospace/",
        "/notes/aerospace/private.txt", "/notes/.hidden.glsl",
        "/projects/shaders/artifacts/generated.glsl",
        "/notes/%2e%2e/.env", "/notes/%2e%2e/projects/shaders/visible.glsl",
        "/notes/%5c..%5c.env",
    )
    for path in denied:
        status, _, body = request(fake_gallery, method, path)
        assert status == 404, path
        assert b"fake-secret" not in body and b"fake-config" not in body
    ####
####


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_link_aliases_do_not_expose_private_files(fake_gallery: Path, method: str) -> None:
    try:
        (fake_gallery / "alias").symlink_to(fake_gallery / ".git", target_is_directory=True)
        (fake_gallery / "notes" / "secret.glsl").symlink_to(fake_gallery / ".env")
        (fake_gallery / "notes" / "linked").symlink_to(fake_gallery / ".git", target_is_directory=True)
        os.link(fake_gallery / ".env", fake_gallery / "notes" / "hardlink.glsl")
    except OSError as error:
        pytest.skip(f"link creation unavailable: {error}")
    ####
    for path in ("/alias/config", "/notes/secret.glsl", "/notes/linked/private.glsl", "/notes/hardlink.glsl"):
        status, _, body = request(fake_gallery, method, path)
        assert status == 404, path
        assert b"fake-secret" not in body and b"fake-config" not in body
    ####
    assert all("secret.glsl" not in item["path"] and "hardlink.glsl" not in item["path"]
               for item in shader_catalog(fake_gallery))
####


@pytest.mark.skipif(not supports_secure_open(), reason="secure descriptor-relative opens unavailable")
def test_shader_catalog_endpoint_returns_only_safe_sources(fake_gallery: Path) -> None:
    status, headers, body = request(fake_gallery, "GET", "/__shader_gallery__/shaders")
    assert status == 200 and headers["Content-Type"] == "application/json; charset=utf-8"
    assert {item["path"] for item in json.loads(body)} == {
        "notes/aerospace/visible.glsl", "projects/shaders/visible.glsl"
    }
    status, _, body = request(fake_gallery, "HEAD", "/__shader_gallery__/shaders")
    assert status == 200 and body == b""
####


@pytest.mark.skipif(not supports_secure_open(), reason="secure descriptor-relative opens unavailable")
def test_swap_after_policy_check_cannot_leak_private_file(
    fake_gallery: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = fake_gallery / "notes/aerospace/visible.glsl"
    original = serve_shader_gallery._allowed_file

    def swap(root: Path, target: str) -> str | None:
        allowed = original(root, target)
        path.unlink()
        path.symlink_to(fake_gallery / ".env")
        return allowed
    ####

    monkeypatch.setattr(serve_shader_gallery, "_allowed_file", swap)
    status, _, body = request(fake_gallery, "GET", "/notes/aerospace/visible.glsl")
    assert status == 404
    assert b"fake-secret" not in body
####


@pytest.mark.skipif(not supports_secure_open(), reason="secure descriptor-relative opens unavailable")
def test_directory_swap_after_policy_check_cannot_leak_private_file(
    fake_gallery: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = fake_gallery / "notes/aerospace"
    original = serve_shader_gallery._allowed_file

    def swap(root: Path, target: str) -> str | None:
        allowed = original(root, target)
        directory.rename(fake_gallery / "notes/original")
        directory.symlink_to(fake_gallery / ".git", target_is_directory=True)
        return allowed
    ####

    monkeypatch.setattr(serve_shader_gallery, "_allowed_file", swap)
    status, _, body = request(fake_gallery, "GET", "/notes/aerospace/private.glsl")
    assert status == 404
    assert b"fake-private-shader" not in body
####


def test_unsupported_platform_fails_closed(
    fake_gallery: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(serve_shader_gallery, "supports_secure_open", lambda: False)
    for method in ("GET", "HEAD"):
        status, _, body = request(fake_gallery, method, "/notes/aerospace/visible.glsl")
        assert status == 404 and b"visible-note-shader" not in body
    ####
    assert shader_catalog(fake_gallery) == []
    monkeypatch.setattr(sys, "argv", ["serve_shader_gallery.py"])
    with pytest.raises(SystemExit) as error:
        serve_shader_gallery.main()
    ####
    assert error.value.code == 2
    assert "requires descriptor-relative no-follow file opens" in capsys.readouterr().err
####
