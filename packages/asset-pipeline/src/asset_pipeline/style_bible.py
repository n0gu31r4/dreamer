"""Style bible: the versioned art-direction contract threaded through every
generation call. Generators are stateless; this file is the consistency weapon.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

BACKGROUND_POLICIES = ("transparent", "opaque")


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    if not _HEX_RE.match(color):
        raise ValueError(f"invalid palette color {color!r}: expected '#RRGGBB'")
    return (int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


@dataclass(frozen=True)
class StyleBible:
    """Palette, grid, background policy, and prompt fragments for one game."""

    name: str
    version: int
    palette: tuple[str, ...]  # normalized "#RRGGBB" strings
    grid: int  # tile/grid unit in pixels
    background: str  # one of BACKGROUND_POLICIES
    prompt_fragments: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("style bible needs a name")
        if not self.palette:
            raise ValueError("style bible needs a non-empty palette")
        normalized = tuple(rgb_to_hex(hex_to_rgb(c)) for c in self.palette)
        object.__setattr__(self, "palette", normalized)
        if self.grid <= 0:
            raise ValueError(f"grid must be positive, got {self.grid}")
        if self.background not in BACKGROUND_POLICIES:
            raise ValueError(
                f"background must be one of {BACKGROUND_POLICIES}, got {self.background!r}"
            )

    @property
    def palette_rgb(self) -> tuple[tuple[int, int, int], ...]:
        return tuple(hex_to_rgb(c) for c in self.palette)

    @classmethod
    def from_dict(cls, data: dict) -> "StyleBible":
        try:
            return cls(
                name=data["name"],
                version=int(data["version"]),
                palette=tuple(data["palette"]),
                grid=int(data["grid"]),
                background=data["background"],
                prompt_fragments=dict(data.get("prompt_fragments", {})),
            )
        except KeyError as e:
            raise ValueError(f"style bible missing required field: {e.args[0]}") from e

    @classmethod
    def load(cls, path: str | Path) -> "StyleBible":
        return cls.from_dict(json.loads(Path(path).read_text()))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "palette": list(self.palette),
            "grid": self.grid,
            "background": self.background,
            "prompt_fragments": dict(self.prompt_fragments),
        }

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2) + "\n")
