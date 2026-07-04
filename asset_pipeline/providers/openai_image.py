"""OpenAI gpt-image-1.5 provider: dreamer's first live generator.

gpt-image-1.5 is the general-2D workhorse with native transparency. We pin
1.5 deliberately: its successor gpt-image-2 is stronger on text/resolution but
DROPPED transparent-background support (`background="transparent"` errors), and
alpha is non-negotiable for sprite cutouts. See PLAN.md / README §5.

The model's smallest output is ~1024px (total pixels >= 655_360, edges multiple
of 16), so it cannot emit a 32x32 sprite directly. We generate at the valid API
size closest to the spec's aspect ratio and let `postprocess` nearest-neighbor
downscale to `spec.size`. True pixel-native sprites come later from a pixel-art
specialist provider.

Live: needs OPENAI_API_KEY and spends money per image. The gate never touches
this — it's exercised only via scripts/smoke_live.py. The `openai` package is a
lazy, optional dependency (the `live` extra), imported only on a real call.
"""

from __future__ import annotations

import base64
import io

from PIL import Image

from ..manifest import AssetSpec
from ..postprocess import TRANSPARENT_CATEGORIES
from ..style_bible import StyleBible
from . import GenerationRequest, GenerationResult, compile_prompt

MODEL = "gpt-image-1.5"

# gpt-image-1.5 only accepts these discrete sizes. We choose by aspect ratio;
# postprocess then downscales to the real spec size.
API_SIZE_SQUARE = "1024x1024"
API_SIZE_PORTRAIT = "1024x1536"
API_SIZE_LANDSCAPE = "1536x1024"


def choose_api_size(spec_size: tuple[int, int]) -> str:
    """Pick the API output size whose aspect ratio best matches the spec, so the
    nearest-neighbor downscale in postprocess doesn't distort proportions."""
    w, h = spec_size
    ratio = w / h
    if ratio >= 1.25:
        return API_SIZE_LANDSCAPE
    if ratio <= 0.8:
        return API_SIZE_PORTRAIT
    return API_SIZE_SQUARE


def background_for(spec: AssetSpec, bible: StyleBible) -> str:
    """`transparent` only when the bible asks for it AND the category is one that
    should be cut out (sprites/ui); everything else is `opaque`."""
    if bible.background == "transparent" and spec.category in TRANSPARENT_CATEGORIES:
        return "transparent"
    return "opaque"


class OpenAIImageProvider:
    """Provider backed by OpenAI's image API. `client` is injectable for tests;
    left None it lazily constructs a real `openai.OpenAI()` (reads OPENAI_API_KEY)."""

    def __init__(self, client=None, model: str = MODEL, quality: str = "high"):
        self._client = client
        self.model = model
        self.name = model
        self.quality = quality

    def _client_or_default(self):
        if self._client is None:
            from openai import OpenAI  # lazy: only needed for a live call

            self._client = OpenAI()
        return self._client

    def generate(self, request: GenerationRequest) -> GenerationResult:
        prompt = compile_prompt(request.spec, request.bible, request.feedback)
        api_size = choose_api_size(request.spec.size)
        background = background_for(request.spec, request.bible)

        response = self._client_or_default().images.generate(
            model=self.model,
            prompt=prompt,
            size=api_size,
            background=background,
            output_format="png",
            quality=self.quality,
            n=1,
        )
        image = Image.open(io.BytesIO(base64.b64decode(response.data[0].b64_json)))
        return GenerationResult(
            image=image.convert("RGBA"),
            provider=self.name,
            prompt=prompt,
            meta={
                "model": self.model,
                "api_size": api_size,
                "background": background,
                "quality": self.quality,
            },
        )
