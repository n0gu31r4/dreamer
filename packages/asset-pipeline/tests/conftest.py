import pytest
from PIL import Image

from asset_pipeline.manifest import AssetSpec
from asset_pipeline.style_bible import StyleBible

# 4-color Nord-ish test palette
PALETTE = ("#2E3440", "#BF616A", "#A3BE8C", "#EBCB8B")
GREEN = (0xA3, 0xBE, 0x8C, 255)  # exactly #A3BE8C
OFF_GREEN = (0xA0, 0xBE, 0x8C, 255)  # slightly off-palette; nearest is #A3BE8C


@pytest.fixture
def bible() -> StyleBible:
    return StyleBible(
        name="test-style",
        version=1,
        palette=PALETTE,
        grid=16,
        background="transparent",
        prompt_fragments={
            "base": "pixel art, crisp pixels, no anti-aliasing",
            "sprite": "single character, full body, centered",
        },
    )


@pytest.fixture
def sprite_spec() -> AssetSpec:
    return AssetSpec(
        id="goblin", category="sprite", size=(32, 32), description="small green goblin"
    )


def make_sprite(
    size: tuple[int, int] = (32, 32),
    fill: tuple[int, int, int, int] = GREEN,
    bg: tuple[int, int, int, int] = (0, 0, 0, 0),
    inset: int = 8,
) -> Image.Image:
    """Centered solid blob of `fill` on `bg` — the minimal deterministic sprite."""
    img = Image.new("RGBA", size, bg)
    for x in range(inset, size[0] - inset):
        for y in range(inset, size[1] - inset):
            img.putpixel((x, y), fill)
    return img


@pytest.fixture
def sprite_factory():
    return make_sprite
