import pytest

from asset_pipeline.manifest import AssetSpec, Manifest, ManifestEntry


def entry(asset_id: str, **kwargs) -> ManifestEntry:
    return ManifestEntry(
        spec=AssetSpec(
            id=asset_id, category="sprite", size=(32, 32), description="a thing"
        ),
        **kwargs,
    )


def test_round_trip(tmp_path):
    manifest = Manifest(entries=[entry("goblin"), entry("slime")])
    path = tmp_path / "manifest.json"
    manifest.save(path)
    loaded = Manifest.load(path)
    assert [e.spec.id for e in loaded.entries] == ["goblin", "slime"]
    assert all(e.status == "pending" for e in loaded.entries)


def test_pending_and_set_result():
    manifest = Manifest(entries=[entry("goblin"), entry("slime")])
    manifest.set_result("goblin", "passed", {"provider": "local"})
    assert [e.spec.id for e in manifest.pending()] == ["slime"]
    assert manifest.get("goblin").provenance == {"provider": "local"}


def test_duplicate_ids_rejected():
    with pytest.raises(ValueError, match="duplicate asset id"):
        Manifest(entries=[entry("goblin"), entry("goblin")])


def test_unknown_asset_raises():
    with pytest.raises(KeyError):
        Manifest(entries=[]).get("nope")


def test_bad_category_rejected():
    with pytest.raises(ValueError, match="category"):
        AssetSpec(id="x", category="weapon", size=(32, 32), description="d")


def test_bad_size_rejected():
    with pytest.raises(ValueError, match="size"):
        AssetSpec(id="x", category="sprite", size=(0, 32), description="d")


def test_bad_status_rejected():
    manifest = Manifest(entries=[entry("goblin")])
    with pytest.raises(ValueError, match="status"):
        manifest.set_result("goblin", "done", {})
