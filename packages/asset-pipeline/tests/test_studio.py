"""The public boundary: everything a caller needs is reachable from `asset_pipeline`
alone, and `Studio` produces a manifest end-to-end without the caller ever touching
a provider or a judge."""

import asset_pipeline
from asset_pipeline import AssetSpec, Manifest, ManifestEntry, Studio

OPAQUE_DARK = (0x2E, 0x34, 0x40, 255)


def test_public_surface_is_reachable_from_package_root():
    # The boundary contract: these are the only names a caller should need.
    for name in ("Studio", "ProductionReport", "StyleBible", "AssetSpec", "Manifest"):
        assert hasattr(asset_pipeline, name), f"{name} missing from public API"
    assert set(asset_pipeline.__all__) >= {"Studio", "StyleBible", "AssetSpec", "Manifest"}


def test_studio_produces_manifest_without_caller_touching_internals(
    tmp_path, bible, sprite_factory
):
    src = tmp_path / "src"
    src.mkdir()
    sprite_factory().save(src / "goblin.png")  # clean transparent sprite -> passes
    sprite_factory(bg=OPAQUE_DARK).save(src / "slime.png")  # opaque bg -> fails checks

    manifest = Manifest(
        entries=[
            ManifestEntry(spec=AssetSpec("goblin", "sprite", (32, 32), "goblin")),
            ManifestEntry(spec=AssetSpec("slime", "sprite", (32, 32), "slime")),
        ]
    )

    studio = Studio.default("local", directory=src)  # no provider/judge in caller code
    report = studio.produce(manifest, bible, tmp_path / "out")

    assert (report.passed, report.failed, report.total) == (1, 1, 2)
    assert report.all_passed is False
    assert manifest.get("goblin").status == "passed"
    assert manifest.get("slime").status == "failed"
    assert (tmp_path / "out" / "goblin.png").exists()


def test_default_factory_rejects_unknown_provider_and_missing_dir():
    import pytest

    with pytest.raises(ValueError, match="unknown provider"):
        Studio.default("midjourney")
    with pytest.raises(ValueError, match="needs directory"):
        Studio.default("local")
