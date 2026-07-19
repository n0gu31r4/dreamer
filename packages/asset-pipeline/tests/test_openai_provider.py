import base64
import io

import pytest
from PIL import Image

from asset_pipeline.manifest import AssetSpec
from asset_pipeline.providers import GenerationRequest
from asset_pipeline.providers.openai_image import (
    API_SIZE_LANDSCAPE,
    API_SIZE_PORTRAIT,
    API_SIZE_SQUARE,
    OpenAIImageProvider,
    background_for,
    choose_api_size,
)
from conftest import make_sprite


def _png_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class _FakeImages:
    """Records the kwargs of the last generate() call and returns a canned PNG."""

    def __init__(self, b64: str, calls: list[dict]):
        self._b64 = b64
        self.calls = calls

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        data = [type("Datum", (), {"b64_json": self._b64})()]
        return type("Response", (), {"data": data})()


class _FakeClient:
    def __init__(self, img: Image.Image):
        self.calls: list[dict] = []
        self.images = _FakeImages(_png_b64(img), self.calls)


def test_choose_api_size_by_aspect_ratio():
    assert choose_api_size((32, 32)) == API_SIZE_SQUARE
    assert choose_api_size((64, 32)) == API_SIZE_LANDSCAPE
    assert choose_api_size((32, 64)) == API_SIZE_PORTRAIT


def test_background_transparent_for_sprite(bible, sprite_spec):
    assert background_for(sprite_spec, bible) == "transparent"


def test_background_opaque_for_background_category(bible):
    spec = AssetSpec(id="sky", category="background", size=(64, 32), description="night sky")
    assert background_for(spec, bible) == "opaque"


def test_background_opaque_when_bible_opaque(sprite_spec):
    from asset_pipeline.style_bible import StyleBible

    opaque_bible = StyleBible(
        name="op", version=1, palette=("#000000",), grid=16, background="opaque"
    )
    assert background_for(sprite_spec, opaque_bible) == "opaque"


def test_generate_returns_rgba_and_provenance(bible, sprite_spec):
    client = _FakeClient(make_sprite())
    provider = OpenAIImageProvider(client=client, quality="medium")

    result = provider.generate(GenerationRequest(sprite_spec, bible))

    assert result.provider == "gpt-image-1.5"
    assert result.image.mode == "RGBA"
    assert "small green goblin" in result.prompt
    assert result.meta == {
        "model": "gpt-image-1.5",
        "api_size": API_SIZE_SQUARE,
        "background": "transparent",
        "quality": "medium",
    }


def test_generate_sends_expected_api_call(bible, sprite_spec):
    client = _FakeClient(make_sprite())
    OpenAIImageProvider(client=client).generate(GenerationRequest(sprite_spec, bible))

    (call,) = client.calls
    assert call["model"] == "gpt-image-1.5"
    assert call["size"] == API_SIZE_SQUARE
    assert call["background"] == "transparent"
    assert call["output_format"] == "png"
    assert call["n"] == 1


def test_construction_requires_no_api_key(monkeypatch):
    # Constructing with an injected client must not import openai or touch env.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIImageProvider(client=_FakeClient(make_sprite()))
    assert provider.name == "gpt-image-1.5"


def test_missing_openai_dep_raises_only_on_live_call(monkeypatch, bible, sprite_spec):
    # No client injected: the lazy `import openai` fires inside generate(), not
    # at construction. None in sys.modules makes the import raise ImportError.
    import sys

    provider = OpenAIImageProvider()
    monkeypatch.setitem(sys.modules, "openai", None)
    with pytest.raises(ImportError):
        provider.generate(GenerationRequest(sprite_spec, bible))
