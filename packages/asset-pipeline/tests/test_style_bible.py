import pytest

from asset_pipeline.style_bible import StyleBible, hex_to_rgb, rgb_to_hex


def test_round_trip(bible, tmp_path):
    path = tmp_path / "bible.json"
    bible.save(path)
    loaded = StyleBible.load(path)
    assert loaded == bible


def test_palette_normalized_to_uppercase():
    b = StyleBible(
        name="x", version=1, palette=("#a3be8c",), grid=16, background="opaque"
    )
    assert b.palette == ("#A3BE8C",)


def test_palette_rgb(bible):
    assert bible.palette_rgb[0] == (0x2E, 0x34, 0x40)


def test_invalid_hex_rejected():
    with pytest.raises(ValueError, match="invalid palette color"):
        StyleBible(name="x", version=1, palette=("#12345",), grid=16, background="opaque")


def test_empty_palette_rejected():
    with pytest.raises(ValueError, match="non-empty palette"):
        StyleBible(name="x", version=1, palette=(), grid=16, background="opaque")


def test_bad_background_rejected():
    with pytest.raises(ValueError, match="background"):
        StyleBible(name="x", version=1, palette=("#000000",), grid=16, background="blue")


def test_missing_field_message(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"name": "x", "version": 1}')
    with pytest.raises(ValueError, match="missing required field: palette"):
        StyleBible.load(path)


def test_hex_rgb_helpers():
    assert hex_to_rgb("#FF0080") == (255, 0, 128)
    assert rgb_to_hex((255, 0, 128)) == "#FF0080"
