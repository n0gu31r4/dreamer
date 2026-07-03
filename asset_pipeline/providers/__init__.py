"""Provider abstraction: image generation behind one interface.

Providers churn (README §Stack); the style-bible threading, post-processing,
and checks are the durable parts. Adding a provider = one new module here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from PIL import Image

from ..manifest import AssetSpec
from ..postprocess import TRANSPARENT_CATEGORIES
from ..style_bible import StyleBible


@dataclass(frozen=True)
class GenerationRequest:
    spec: AssetSpec
    bible: StyleBible
    attempt: int = 1
    feedback: str | None = None  # failure summary from the previous attempt


@dataclass
class GenerationResult:
    image: Image.Image
    provider: str
    prompt: str
    meta: dict = field(default_factory=dict)  # seed, model, etc.


class Provider(Protocol):
    name: str

    def generate(self, request: GenerationRequest) -> GenerationResult: ...


def compile_prompt(spec: AssetSpec, bible: StyleBible, feedback: str | None = None) -> str:
    """Assemble the generation prompt: style bible fragments + asset spec.

    Deterministic text assembly — recorded in provenance so any asset can be
    traced back to exactly what was asked for.
    """
    w, h = spec.size
    parts = [
        bible.prompt_fragments.get("base", ""),
        bible.prompt_fragments.get(spec.category, ""),
        spec.description,
        f"target size {w}x{h} pixels",
        "strict palette: " + ", ".join(bible.palette),
    ]
    if bible.background == "transparent" and spec.category in TRANSPARENT_CATEGORIES:
        parts.append("isolated subject on a fully transparent background")
    if feedback:
        parts.append(f"previous attempt was rejected: {feedback}")
    return ", ".join(p for p in parts if p)
