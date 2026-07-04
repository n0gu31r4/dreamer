from asset_pipeline.godot_import import (
    FILTER_PROJECT_SETTING,
    PIXEL_ART_PARAMS,
    import_file_contents,
    write_import_file,
)


def test_contents_carry_pixel_art_params():
    text = import_file_contents("res://goblin.png")
    assert 'importer="texture"' in text
    assert 'type="CompressedTexture2D"' in text
    assert 'source_file="res://goblin.png"' in text
    # the three settings that keep pixel art crisp
    assert "compress/mode=0" in text
    assert "mipmaps/generate=false" in text  # bool renders lowercase, not "False"
    assert "detect_3d/compress_to=0" in text


def test_params_match_declared_constants():
    text = import_file_contents("res://x.png")
    for key in PIXEL_ART_PARAMS:
        assert key in text


def test_filter_is_a_project_setting_not_an_import_param():
    # Filtering can't live in a .import in Godot 4 — it's project-level.
    setting, value = FILTER_PROJECT_SETTING
    assert setting == "rendering/textures/canvas_textures/default_texture_filter"
    assert value == 0  # Nearest
    assert "filter" not in import_file_contents("res://x.png")


def test_write_import_file_default_res_path(tmp_path):
    png = tmp_path / "hero.png"
    png.write_bytes(b"")  # content irrelevant; we only sidecar it
    sidecar = write_import_file(png)

    assert sidecar == tmp_path / "hero.png.import"
    assert 'source_file="res://hero.png"' in sidecar.read_text()


def test_write_import_file_custom_res_path(tmp_path):
    png = tmp_path / "hero.png"
    png.write_bytes(b"")
    sidecar = write_import_file(png, res_path="res://assets/sprites/hero.png")

    assert 'source_file="res://assets/sprites/hero.png"' in sidecar.read_text()
