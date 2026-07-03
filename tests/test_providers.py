import pytest

from asset_pipeline.manifest import AssetSpec
from asset_pipeline.providers import GenerationRequest, compile_prompt
from asset_pipeline.providers.local import LocalFileProvider
from conftest import make_sprite


def test_prompt_includes_spec_and_bible(bible, sprite_spec):
    prompt = compile_prompt(sprite_spec, bible)
    assert "small green goblin" in prompt
    assert "32x32" in prompt
    assert "#A3BE8C" in prompt  # palette threaded through
    assert "pixel art" in prompt  # base fragment
    assert "transparent background" in prompt


def test_prompt_no_transparency_for_background_category(bible):
    spec = AssetSpec(id="sky", category="background", size=(64, 32), description="night sky")
    assert "transparent background" not in compile_prompt(spec, bible)


def test_prompt_appends_feedback(bible, sprite_spec):
    prompt = compile_prompt(sprite_spec, bible, feedback="palette: 3 pixels off-palette")
    assert prompt.endswith("previous attempt was rejected: palette: 3 pixels off-palette")


def test_local_provider_reads_file(tmp_path, bible, sprite_spec):
    make_sprite().save(tmp_path / "goblin.png")
    result = LocalFileProvider(tmp_path).generate(GenerationRequest(sprite_spec, bible))
    assert result.provider == "local"
    assert result.image.size == (32, 32)
    assert "goblin" in result.prompt
    assert result.meta["source_file"].endswith("goblin.png")


def test_local_provider_missing_file(tmp_path, bible, sprite_spec):
    with pytest.raises(FileNotFoundError, match="goblin"):
        LocalFileProvider(tmp_path).generate(GenerationRequest(sprite_spec, bible))
