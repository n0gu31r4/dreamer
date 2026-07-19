from PIL import Image

from asset_pipeline.manifest import AssetSpec
from asset_pipeline.providers import GenerationRequest
from asset_pipeline.providers.local_sd import (
    CHECKPOINT,
    GEN_SIZE_LANDSCAPE,
    GEN_SIZE_PORTRAIT,
    GEN_SIZE_SQUARE,
    LORA,
    REMBG_NODE,
    LocalSDProvider,
    build_workflow,
    choose_gen_size,
    seed_for,
)
from conftest import make_sprite


class _FakeComfyClient:
    """Records the workflow of the last run_workflow call, returns a canned RGBA
    image — the whole HTTP round-trip mocked, so no ComfyUI server is needed."""

    def __init__(self, img: Image.Image):
        self._img = img
        self.workflows: list[dict] = []

    def run_workflow(self, workflow: dict) -> Image.Image:
        self.workflows.append(workflow)
        return self._img


def test_choose_gen_size_by_aspect_ratio():
    assert choose_gen_size((32, 32)) == GEN_SIZE_SQUARE
    assert choose_gen_size((64, 32)) == GEN_SIZE_LANDSCAPE
    assert choose_gen_size((32, 64)) == GEN_SIZE_PORTRAIT


def test_seed_is_deterministic_but_varies_per_attempt():
    assert seed_for("goblin", 1) == seed_for("goblin", 1)  # reproducible
    assert seed_for("goblin", 1) != seed_for("goblin", 2)  # retry rolls anew
    assert seed_for("goblin", 1) != seed_for("slime", 1)  # differs per asset
    assert 0 <= seed_for("goblin", 1) < 2**32  # a valid 32-bit seed


def test_build_workflow_wires_lora_and_ends_in_rembg_then_save():
    wf = build_workflow(
        positive="a goblin",
        negative="blurry",
        width=1024,
        height=1024,
        seed=42,
        steps=25,
        cfg=7.0,
        sampler="euler",
        scheduler="normal",
    )
    # checkpoint + Pixel Art XL LoRA at full strength
    assert wf["4"]["class_type"] == "CheckpointLoaderSimple"
    assert wf["4"]["inputs"]["ckpt_name"] == CHECKPOINT
    assert wf["5"]["class_type"] == "LoraLoader"
    assert wf["5"]["inputs"]["lora_name"] == LORA
    assert wf["5"]["inputs"]["strength_model"] == 1.0
    # positive/negative encode against the LoRA'd CLIP
    assert wf["6"]["inputs"]["text"] == "a goblin"
    assert wf["7"]["inputs"]["text"] == "blurry"
    assert wf["6"]["inputs"]["clip"] == ["5", 1]
    # sampler pulls the LoRA'd model + both conditionings + seed/size
    assert wf["3"]["inputs"]["seed"] == 42
    assert wf["3"]["inputs"]["positive"] == ["6", 0]
    assert wf["3"]["inputs"]["negative"] == ["7", 0]
    assert wf["8"]["inputs"] == {"width": 1024, "height": 1024, "batch_size": 1}
    # the alpha step: rembg consumes the VAE decode and feeds SaveImage
    assert wf["11"]["class_type"] == REMBG_NODE
    assert wf["11"]["inputs"]["image"] == ["10", 0]
    assert wf["9"]["class_type"] == "SaveImage"
    assert wf["9"]["inputs"]["images"] == ["11", 0]


def test_generate_returns_rgba_and_provenance(bible, sprite_spec):
    client = _FakeComfyClient(make_sprite())
    provider = LocalSDProvider(client=client, steps=30, cfg=6.5)

    result = provider.generate(GenerationRequest(sprite_spec, bible))

    assert result.provider == "local_sd"
    assert result.image.mode == "RGBA"
    assert "small green goblin" in result.prompt
    assert result.meta["gen_size"] == "1024x1024"
    assert result.meta["seed"] == seed_for("goblin", 1)
    assert result.meta["lora"] == LORA
    assert result.meta["background_removal"] == "rembg"
    assert (result.meta["steps"], result.meta["cfg"]) == (30, 6.5)


def test_generate_sends_the_compiled_prompt_and_seed_into_the_workflow(bible, sprite_spec):
    client = _FakeComfyClient(make_sprite())
    provider = LocalSDProvider(client=client)

    result = provider.generate(GenerationRequest(sprite_spec, bible))

    (wf,) = client.workflows
    assert wf["6"]["inputs"]["text"] == result.prompt  # compiled prompt, not raw
    assert wf["3"]["inputs"]["seed"] == seed_for("goblin", 1)
    assert wf["8"]["inputs"]["width"] == 1024


def test_feedback_and_attempt_change_prompt_and_seed(bible, sprite_spec):
    client = _FakeComfyClient(make_sprite())
    provider = LocalSDProvider(client=client)

    provider.generate(GenerationRequest(sprite_spec, bible, attempt=2, feedback="too blurry"))

    (wf,) = client.workflows
    assert "too blurry" in wf["6"]["inputs"]["text"]
    assert wf["3"]["inputs"]["seed"] == seed_for("goblin", 2)  # retry rolled a new seed


def test_injected_client_means_no_server_contact_on_construction():
    # An injected client is used as-is; no ComfyUIClient is built, nothing
    # touches the network until generate() actually calls run_workflow.
    client = _FakeComfyClient(make_sprite())
    provider = LocalSDProvider(client=client)
    assert provider.name == "local_sd"
    assert provider._client_or_default() is client
    assert client.workflows == []  # construction alone contacted nothing
