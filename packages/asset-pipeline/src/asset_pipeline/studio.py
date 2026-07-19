"""Studio: the asset pipeline's single public front door — the black box's mouth.

The orchestrator (or any caller) touches *only* this. It hands over a structured
request — a `StyleBible` (art-direction contract) + a `Manifest` of `AssetSpec`s
(what the game needs) + an output dir — and gets back a `ProductionReport` plus a
manifest updated in place with full provenance. Everything the box does inside —
which provider makes which asset, prompt compilation, post-processing, the
deterministic checks, the regenerate-with-feedback loop, vision QA — is hidden
behind this seam.

Boundary rule (see asset_pipeline/README.md): callers import from `asset_pipeline`
only. `providers`, `postprocess`, `checks`, `qa`, `pipeline` are internal
implementation and may change without notice — the orchestrator never constructs
a provider or a judge itself; `Studio.default(...)` does that for it.

Provider routing (☐ INTENT): per-asset-class routing — pixel-art sprites and
animation to the local SDXL specialist, backgrounds/UI to gpt-image-1.5 — lands
with the `local_sd` provider (Milestone 3). Today a Studio runs one configured
provider for every asset; when a second real generator exists, routing becomes a
`_provider_for(spec)` seam inside this class, invisible to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .manifest import Manifest
from .pipeline import run_manifest
from .providers import Provider
from .qa import StubJudge, VisionJudge
from .style_bible import StyleBible


@dataclass(frozen=True)
class ProductionReport:
    """Structured result of producing a manifest's assets.

    The counts summarize; per-asset detail (prompt, checks, verdict, file) lives
    in each manifest entry's provenance, which `produce` updates in place.
    """

    passed: int
    failed: int

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def all_passed(self) -> bool:
        return self.passed > 0 and self.failed == 0


class Studio:
    """The asset pipeline as a black box.

    Construct with a provider, or use `Studio.default(...)` so the caller never
    has to import the providers subpackage. The vision judge defaults to the
    current no-op stub (deterministic checks are the only real eyes in v1) until
    the visual-eval leg lands.
    """

    def __init__(
        self,
        provider: Provider,
        *,
        judge: VisionJudge | None = None,
        max_attempts: int = 2,
    ):
        self._provider = provider
        self._judge = judge or StubJudge()
        self._max_attempts = max_attempts

    @classmethod
    def default(cls, provider: str = "openai", **provider_opts) -> "Studio":
        """Build a Studio for a named provider without importing providers directly.

        `"openai"` -> gpt-image-1.5, the general-2D generator (needs
        OPENAI_API_KEY, spends money per image); `"local"` -> the local-file
        provider that reads pre-made PNGs from `directory=...` (offline, for
        tests and hand-drawn assets). `"local_sd"` (pixel-art specialist) arrives
        with Milestone 3.
        """
        return cls(_build_provider(provider, **provider_opts))

    def produce(
        self, manifest: Manifest, bible: StyleBible, out_dir: str | Path
    ) -> ProductionReport:
        """Produce every pending asset in the manifest.

        Updates `manifest` in place (each entry gets status + provenance) and
        returns a summary. Provider errors are recorded per asset, never raised —
        one bad asset does not sink the batch.
        """
        counts = run_manifest(
            manifest, bible, self._provider, self._judge, out_dir, self._max_attempts
        )
        return ProductionReport(passed=counts["passed"], failed=counts["failed"])


def _build_provider(name: str, **opts) -> Provider:
    """Provider factory — the one place that knows concrete provider classes, so
    callers don't. Imports are local so an unused provider's deps stay unloaded
    (e.g. the `openai` SDK is only imported when you actually ask for it)."""
    key = name.lower()
    if key == "openai":
        from .providers.openai_image import OpenAIImageProvider

        return OpenAIImageProvider(**opts)
    if key == "local":
        from .providers.local import LocalFileProvider

        try:
            directory = opts.pop("directory")
        except KeyError:
            raise ValueError("local provider needs directory=<path to pre-made PNGs>")
        return LocalFileProvider(directory, **opts)
    raise ValueError(f"unknown provider {name!r}; known: 'openai', 'local'")
