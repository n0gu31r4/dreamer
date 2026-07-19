"""Vision QA interface: the judge slot for the visual-eval leg.

The interface exists now so the pipeline shape is final; the real vision judge
(Claude reviewing the asset in-engine against a checklist) lands with the
visual-eval leg. Until then StubJudge passes everything and says so loudly
in provenance — deterministic checks are the only real eyes in v1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from PIL import Image

from .manifest import AssetSpec
from .style_bible import StyleBible


@dataclass(frozen=True)
class Verdict:
    passed: bool
    notes: str
    source: str  # which judge produced this

    def to_dict(self) -> dict:
        return {"passed": self.passed, "notes": self.notes, "source": self.source}


class VisionJudge(Protocol):
    def review(self, image: Image.Image, spec: AssetSpec, bible: StyleBible) -> Verdict: ...


class StubJudge:
    """Always passes. Placeholder until the visual-eval leg exists."""

    def review(self, image: Image.Image, spec: AssetSpec, bible: StyleBible) -> Verdict:
        return Verdict(
            passed=True,
            notes="vision-eval leg not built; deterministic checks only",
            source="stub",
        )
