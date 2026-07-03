"""Deterministic post-processing: same input, same output, every time.

No model judgment lives here. These transforms convert raw provider output
into gate-checkable assets: exact size, exact palette, binary alpha.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from .manifest import AssetSpec
from .style_bible import StyleBible

# Alpha at or above this is snapped to fully opaque; below, fully transparent.
ALPHA_THRESHOLD = 128

# Categories that must end up on a transparent background when the bible
# says background="transparent". Backgrounds are full-bleed; tilesets vary.
TRANSPARENT_CATEGORIES = ("sprite", "ui")


@dataclass
class PostprocessResult:
    image: Image.Image
    notes: list[str] = field(default_factory=list)


def ensure_rgba(img: Image.Image) -> Image.Image:
    return img if img.mode == "RGBA" else img.convert("RGBA")


def scale_to_size(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Nearest-neighbor resize — the only resampling that preserves pixel art."""
    if img.size == size:
        return img
    return img.resize(size, Image.NEAREST)


def snap_alpha(img: Image.Image, threshold: int = ALPHA_THRESHOLD) -> Image.Image:
    """Binarize alpha: no semi-transparent fringe pixels survive."""
    img = ensure_rgba(img)
    out = img.copy()
    out.putdata(
        [(r, g, b, 255 if a >= threshold else 0) for r, g, b, a in img.get_flattened_data()]
    )
    return out


def quantize_to_palette(
    img: Image.Image, palette_rgb: tuple[tuple[int, int, int], ...]
) -> Image.Image:
    """Map every opaque pixel to its nearest palette color (Euclidean RGB).

    This is what turns "style consistency" from a taste judgment into a
    machine-checkable property: after this, check_palette must pass.
    """
    img = ensure_rgba(img)
    cache: dict[tuple[int, int, int], tuple[int, int, int]] = {}

    def nearest(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
        if rgb not in cache:
            cache[rgb] = min(
                palette_rgb,
                key=lambda p: (p[0] - rgb[0]) ** 2
                + (p[1] - rgb[1]) ** 2
                + (p[2] - rgb[2]) ** 2,
            )
        return cache[rgb]

    out = img.copy()
    out.putdata(
        [
            (*nearest((r, g, b)), a) if a > 0 else (0, 0, 0, 0)
            for r, g, b, a in img.get_flattened_data()
        ]
    )
    return out


def postprocess(img: Image.Image, spec: AssetSpec, bible: StyleBible) -> PostprocessResult:
    """Full pipeline: RGBA -> target size -> alpha snap -> palette quantize."""
    notes: list[str] = []

    out = ensure_rgba(img)
    if out.size != spec.size:
        notes.append(f"resized {out.size[0]}x{out.size[1]} -> {spec.size[0]}x{spec.size[1]}")
        out = scale_to_size(out, spec.size)

    out = snap_alpha(out)
    out = quantize_to_palette(out, bible.palette_rgb)
    notes.append(f"quantized to {len(bible.palette)}-color palette")

    return PostprocessResult(image=out, notes=notes)
