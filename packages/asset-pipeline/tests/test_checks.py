from asset_pipeline.checks import check_grid, run_checks
from asset_pipeline.manifest import AssetSpec
from conftest import GREEN, make_sprite

OPAQUE_DARK = (0x2E, 0x34, 0x40, 255)  # #2E3440, on-palette but opaque


def test_conformant_sprite_passes_all(bible, sprite_spec):
    report = run_checks(make_sprite(), sprite_spec, bible)
    assert report.passed
    assert report.summary() == "all checks passed"


def test_wrong_dimensions_fail(bible, sprite_spec):
    report = run_checks(make_sprite(size=(16, 16), inset=4), sprite_spec, bible)
    assert "dimensions" in {r.name for r in report.failures}


def test_opaque_background_fails_for_sprite(bible, sprite_spec):
    report = run_checks(make_sprite(bg=OPAQUE_DARK), sprite_spec, bible)
    assert {r.name for r in report.failures} == {"transparent_background"}


def test_opaque_background_ok_for_background_category(bible):
    spec = AssetSpec(id="sky", category="background", size=(32, 32), description="sky")
    report = run_checks(make_sprite(bg=OPAQUE_DARK), spec, bible)
    assert report.passed


def test_off_palette_pixels_fail(bible, sprite_spec):
    report = run_checks(make_sprite(fill=(1, 2, 3, 255)), sprite_spec, bible)
    assert {r.name for r in report.failures} == {"palette"}
    assert "off-palette" in report.summary()


def test_tileset_grid_alignment(bible):
    aligned = AssetSpec(id="t1", category="tileset", size=(48, 48), description="walls")
    misaligned = AssetSpec(id="t2", category="tileset", size=(40, 40), description="walls")
    assert check_grid(make_sprite(size=(48, 48), bg=GREEN), aligned, bible).passed
    assert not check_grid(make_sprite(size=(40, 40), bg=GREEN), misaligned, bible).passed
