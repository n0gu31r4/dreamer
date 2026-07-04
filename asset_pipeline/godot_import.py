"""Godot 4 import sidecars: make generated PNGs import as crisp pixel art.

Godot writes a `<file>.import` next to every texture on first import. If we
ship one ourselves, we own the settings that matter for pixel art. Godot
reads our `[params]` on import, applies them, and rewrites the cache stanzas
(`uid`, dest paths) itself — so we only need to author the params.

Three settings carry the intent:
  - compress/mode=0        -> Lossless (VRAM compression smears pixel art)
  - mipmaps/generate=false -> mipmaps blur sprites when scaled down
  - detect_3d/compress_to=0 -> Disabled; otherwise Godot silently switches a
                              texture to VRAM+mipmaps the moment it's seen in 3D.

Nearest-neighbor *filtering* is deliberately absent: in Godot 4 it is NOT a
per-texture import setting. It's the project-level
`rendering/textures/canvas_textures/default_texture_filter`, which the
consuming project must set to Nearest (0). Exposed as FILTER_PROJECT_SETTING
so callers can surface it to the human.
"""

from __future__ import annotations

from pathlib import Path

# Only the pixel-art-critical keys. Godot fills defaults for everything else on
# (re)import and preserves these.
PIXEL_ART_PARAMS: dict[str, object] = {
    "compress/mode": 0,
    "mipmaps/generate": False,
    "detect_3d/compress_to": 0,
}

# The one thing a .import file can't carry — a project setting the game must set.
FILTER_PROJECT_SETTING = ("rendering/textures/canvas_textures/default_texture_filter", 0)


def _gd_value(value: object) -> str:
    """Render a Python value as a Godot resource literal."""
    if isinstance(value, bool):  # bool before int: True is an int subclass
        return "true" if value else "false"
    return str(value)


def import_file_contents(png_res_path: str) -> str:
    """The text of a pixel-art `.import` sidecar for a PNG at `png_res_path`
    (a Godot `res://...` path)."""
    lines = [
        "[remap]",
        "",
        'importer="texture"',
        'type="CompressedTexture2D"',
        "",
        "[deps]",
        "",
        f'source_file="{png_res_path}"',
        "",
        "[params]",
        "",
        *(f"{k}={_gd_value(v)}" for k, v in PIXEL_ART_PARAMS.items()),
    ]
    return "\n".join(lines) + "\n"


def write_import_file(png_path: str | Path, res_path: str | None = None) -> Path:
    """Write `<png>.import` next to a generated PNG. `res_path` is the PNG's
    Godot `res://` path (defaults to `res://<filename>`). Returns the sidecar path."""
    png_path = Path(png_path)
    if res_path is None:
        res_path = f"res://{png_path.name}"
    import_path = png_path.with_name(png_path.name + ".import")
    import_path.write_text(import_file_contents(res_path))
    return import_path
