"""Dreamer's asset pipeline — a black box: asset requests in, checked assets out.

Manifest-driven 2D asset generation for Godot games:
    generate -> post-process -> deterministic checks -> vision QA -> ledger.

Division of labor (see README §5): image generation is provider-pluggable;
Claude/vision is the *judge*, never the pixel generator; every property that
can be computed is asserted in code, and vision judges only the residue.

Public API (the boundary — see asset_pipeline/README.md): callers touch only the
names re-exported here. `Studio` is the single entry point; the request contract
is a `StyleBible` + a `Manifest` of `AssetSpec`s. Everything else — `providers`,
`postprocess`, `checks`, `qa`, `pipeline` — is internal and may change freely.
"""

from .manifest import AssetSpec, Manifest, ManifestEntry
from .studio import ProductionReport, Studio
from .style_bible import StyleBible

__version__ = "0.1.0"

__all__ = [
    "Studio",
    "ProductionReport",
    "StyleBible",
    "AssetSpec",
    "Manifest",
    "ManifestEntry",
    "__version__",
]
