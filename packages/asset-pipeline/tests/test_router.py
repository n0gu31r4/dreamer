from asset_pipeline import AssetSpec, Manifest, ManifestEntry, Studio
from asset_pipeline.providers import GenerationRequest, GenerationResult
from asset_pipeline.providers.router import CategoryRouter
from conftest import make_sprite


class _StampProvider:
    """A stand-in provider that stamps its own name into the result, so we can
    prove which sub-provider a request reached."""

    def __init__(self, name: str):
        self.name = name

    def generate(self, request: GenerationRequest) -> GenerationResult:
        return GenerationResult(
            image=make_sprite(), provider=self.name, prompt="p", meta={}
        )


def _spec(category: str) -> AssetSpec:
    return AssetSpec(id=category, category=category, size=(32, 32), description="x")


def test_router_sends_each_category_to_its_provider():
    specialist = _StampProvider("local_sd")
    general = _StampProvider("openai")
    router = CategoryRouter(routes={"sprite": specialist}, default=general)

    assert router.provider_for(_spec("sprite")) is specialist
    assert router.provider_for(_spec("background")) is general  # default
    assert router.provider_for(_spec("ui")) is general
    assert router.generate(GenerationRequest(_spec("sprite"), None)).provider == "local_sd"
    assert router.generate(GenerationRequest(_spec("background"), None)).provider == "openai"


def test_studio_routed_records_the_real_generator_per_asset(tmp_path, bible):
    # Route via the local-file provider for sprites and a distinct one for the
    # rest, then check each asset's provenance names the provider that made it.
    src = tmp_path / "src"
    src.mkdir()
    make_sprite().save(src / "hero.png")
    make_sprite().save(src / "sky.png")

    studio = Studio.routed(
        sprite="local",
        generalist="local",
        sprite_opts={"directory": src},
        generalist_opts={"directory": src},
    )
    manifest = Manifest(
        entries=[
            ManifestEntry(spec=AssetSpec("hero", "sprite", (32, 32), "hero")),
            ManifestEntry(spec=AssetSpec("sky", "background", (32, 32), "sky")),
        ]
    )

    report = studio.produce(manifest, bible, tmp_path / "out")

    assert report.passed == 2
    # both came from the local-file provider; the attempt record names it
    hero_prov = manifest.get("hero").provenance
    assert hero_prov["provider"] == "category-router"  # top-level wrapper
    assert hero_prov["attempts"][0]["provider"] == "local"  # concrete generator
