"""Per-asset-class routing: send each request to the right specialist.

The pixel-art specialist (`local_sd`) makes sprites; the generalist
(`gpt-image-1.5`) makes backgrounds/UI/everything-else. This is the seam the
Studio docstring has promised since Milestone 3 was scoped. It is deliberately a
plain category -> provider map with a default, *not* a routing framework — the
whole point of the black box is that the caller never sees it.

A `CategoryRouter` is itself a `Provider` (same `name` + `generate`), so the
pipeline runner stays completely unchanged: it is handed one provider and calls
`generate`; the router forwards to the chosen sub-provider, whose real name
(`local_sd` / `gpt-image-1.5`) lands in each attempt's provenance.
"""

from __future__ import annotations

from ..manifest import AssetSpec
from . import GenerationRequest, GenerationResult, Provider


class CategoryRouter:
    """Dispatch by `spec.category`, falling back to `default` for anything not in
    the map. Construct with already-built providers so it's trivially testable
    with fakes and holds no knowledge of how providers are made."""

    def __init__(self, routes: dict[str, Provider], default: Provider):
        self._routes = dict(routes)
        self._default = default
        self.name = "category-router"

    def provider_for(self, spec: AssetSpec) -> Provider:
        return self._routes.get(spec.category, self._default)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        return self.provider_for(request.spec).generate(request)
