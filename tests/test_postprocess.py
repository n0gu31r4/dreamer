from PIL import Image

from asset_pipeline.postprocess import (
    postprocess,
    quantize_to_palette,
    scale_to_size,
    snap_alpha,
)
from conftest import GREEN, OFF_GREEN, make_sprite


def test_quantize_maps_off_palette_to_nearest(bible):
    img = make_sprite(fill=OFF_GREEN)
    out = quantize_to_palette(img, bible.palette_rgb)
    assert out.getpixel((16, 16)) == GREEN


def test_quantize_preserves_transparency(bible):
    out = quantize_to_palette(make_sprite(), bible.palette_rgb)
    assert out.getpixel((0, 0)) == (0, 0, 0, 0)


def test_snap_alpha_binarizes():
    img = Image.new("RGBA", (2, 1))
    img.putpixel((0, 0), (10, 10, 10, 200))
    img.putpixel((1, 0), (10, 10, 10, 100))
    out = snap_alpha(img)
    assert out.getpixel((0, 0))[3] == 255
    assert out.getpixel((1, 0))[3] == 0


def test_scale_nearest_introduces_no_new_colors():
    big = make_sprite(size=(64, 64), inset=16)
    out = scale_to_size(big, (32, 32))
    colors = {color for _, color in out.getcolors()}
    assert colors <= {GREEN, (0, 0, 0, 0)}


def test_postprocess_resizes_quantizes_and_notes(bible, sprite_spec):
    raw = make_sprite(size=(64, 64), fill=OFF_GREEN, inset=16)
    result = postprocess(raw, sprite_spec, bible)
    assert result.image.size == (32, 32)
    assert any("resized" in n for n in result.notes)
    assert result.image.getpixel((16, 16)) == GREEN
