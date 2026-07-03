"""Deterministic checks: every measurable property is an assert, not a judgment.

These run in the gate. Vision QA (qa.py) judges only what these cannot compute.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from .manifest import AssetSpec
from .postprocess import TRANSPARENT_CATEGORIES, ensure_rgba
from .style_bible import StyleBible, rgb_to_hex

# Minimum fraction of border pixels that must be transparent for an asset
# that requires a transparent background (sprites are centered subjects).
BORDER_TRANSPARENCY_MIN = 0.5


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    details: str

    def to_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed, "details": self.details}


@dataclass
class CheckReport:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if not r.passed]

    def summary(self) -> str:
        if self.passed:
            return "all checks passed"
        return "; ".join(f"{r.name}: {r.details}" for r in self.failures)

    def to_dict(self) -> dict:
        return {"passed": self.passed, "results": [r.to_dict() for r in self.results]}


def check_dimensions(img: Image.Image, spec: AssetSpec) -> CheckResult:
    ok = img.size == spec.size
    return CheckResult(
        name="dimensions",
        passed=ok,
        details=f"expected {spec.size[0]}x{spec.size[1]}, got {img.size[0]}x{img.size[1]}",
    )


def check_transparent_background(img: Image.Image, spec: AssetSpec, bible: StyleBible) -> CheckResult:
    """Assets that need alpha must actually have a mostly-transparent border."""
    applies = bible.background == "transparent" and spec.category in TRANSPARENT_CATEGORIES
    if not applies:
        return CheckResult("transparent_background", True, "not required for this asset")

    img = ensure_rgba(img)
    w, h = img.size
    pixels = img.load()
    border = (
        [(x, 0) for x in range(w)]
        + [(x, h - 1) for x in range(w)]
        + [(0, y) for y in range(1, h - 1)]
        + [(w - 1, y) for y in range(1, h - 1)]
    )
    transparent = sum(1 for x, y in border if pixels[x, y][3] == 0)
    ratio = transparent / len(border)
    return CheckResult(
        name="transparent_background",
        passed=ratio >= BORDER_TRANSPARENCY_MIN,
        details=f"{ratio:.0%} of border transparent (need >= {BORDER_TRANSPARENCY_MIN:.0%})",
    )


def check_palette(img: Image.Image, bible: StyleBible) -> CheckResult:
    """Every visible pixel must be exactly a palette color. Vision can't do this;
    three lines of code can."""
    img = ensure_rgba(img)
    palette = set(bible.palette_rgb)
    offenders: dict[tuple[int, int, int], int] = {}
    for r, g, b, a in img.get_flattened_data():
        if a > 0 and (r, g, b) not in palette:
            offenders[(r, g, b)] = offenders.get((r, g, b), 0) + 1
    if not offenders:
        return CheckResult("palette", True, f"all pixels within {len(palette)}-color palette")
    sample = ", ".join(rgb_to_hex(c) for c in list(offenders)[:5])
    return CheckResult(
        name="palette",
        passed=False,
        details=f"{sum(offenders.values())} pixels off-palette ({len(offenders)} colors, e.g. {sample})",
    )


def check_grid(img: Image.Image, spec: AssetSpec, bible: StyleBible) -> CheckResult:
    """Tilesets must be an exact multiple of the grid unit."""
    if spec.category != "tileset":
        return CheckResult("grid", True, "not a tileset")
    w, h = img.size
    ok = w % bible.grid == 0 and h % bible.grid == 0
    return CheckResult(
        name="grid",
        passed=ok,
        details=f"{w}x{h} vs grid {bible.grid} ({'aligned' if ok else 'misaligned'})",
    )


def run_checks(img: Image.Image, spec: AssetSpec, bible: StyleBible) -> CheckReport:
    return CheckReport(
        results=[
            check_dimensions(img, spec),
            check_transparent_background(img, spec, bible),
            check_palette(img, bible),
            check_grid(img, spec, bible),
        ]
    )
