from asset_pipeline.manifest import AssetSpec, Manifest, ManifestEntry
from asset_pipeline.pipeline import run_asset, run_manifest
from asset_pipeline.providers.local import LocalFileProvider
from asset_pipeline.qa import StubJudge
from conftest import OFF_GREEN, make_sprite

OPAQUE_DARK = (0x2E, 0x34, 0x40, 255)


def test_good_asset_passes_end_to_end(tmp_path, bible, sprite_spec):
    src = tmp_path / "src"
    src.mkdir()
    # raw is oversized and slightly off-palette: post-processing must fix both
    make_sprite(size=(64, 64), fill=OFF_GREEN, inset=16).save(src / "goblin.png")

    status, prov = run_asset(
        sprite_spec, bible, LocalFileProvider(src), StubJudge(), tmp_path / "out"
    )

    assert status == "passed"
    assert (tmp_path / "out" / "goblin.png").exists()
    assert prov["provider"] == "local"
    assert prov["attempts"][0]["checks"]["passed"] is True
    assert prov["attempts"][0]["verdict"]["source"] == "stub"
    assert prov["file"].endswith("goblin.png")


def test_bad_asset_fails_and_retry_carries_feedback(tmp_path, bible, sprite_spec):
    src = tmp_path / "src"
    src.mkdir()
    make_sprite(bg=OPAQUE_DARK).save(src / "goblin.png")  # opaque background

    status, prov = run_asset(
        sprite_spec, bible, LocalFileProvider(src), StubJudge(), tmp_path / "out",
        max_attempts=2,
    )

    assert status == "failed"
    assert len(prov["attempts"]) == 2
    # the regenerate-with-critique hook: attempt 2's prompt carries attempt 1's failure
    assert "previous attempt was rejected" in prov["attempts"][1]["prompt"]
    assert "transparent" in prov["attempts"][1]["prompt"]
    assert not (tmp_path / "out" / "goblin.png").exists()


def test_provider_error_recorded_not_raised(tmp_path, bible, sprite_spec):
    status, prov = run_asset(
        sprite_spec, bible, LocalFileProvider(tmp_path), StubJudge(), tmp_path / "out"
    )
    assert status == "failed"
    assert "FileNotFoundError" in prov["attempts"][0]["error"]


def test_run_manifest_updates_ledger(tmp_path, bible):
    good = AssetSpec(id="goblin", category="sprite", size=(32, 32), description="goblin")
    bad = AssetSpec(id="slime", category="sprite", size=(32, 32), description="slime")
    src = tmp_path / "src"
    src.mkdir()
    make_sprite().save(src / "goblin.png")
    make_sprite(bg=OPAQUE_DARK).save(src / "slime.png")
    manifest = Manifest(entries=[ManifestEntry(spec=good), ManifestEntry(spec=bad)])

    counts = run_manifest(
        manifest, bible, LocalFileProvider(src), StubJudge(), tmp_path / "out"
    )

    assert counts == {"passed": 1, "failed": 1}
    assert manifest.get("goblin").status == "passed"
    assert manifest.get("slime").status == "failed"
    assert manifest.pending() == []

    # ledger survives a round trip
    path = tmp_path / "manifest.json"
    manifest.save(path)
    assert Manifest.load(path).get("goblin").provenance["file"].endswith("goblin.png")
