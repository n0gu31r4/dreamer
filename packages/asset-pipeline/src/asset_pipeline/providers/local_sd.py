"""Local SDXL + Pixel Art XL provider: dreamer's pixel-art *specialist*.

Runs against a local ComfyUI server (SDXL base + the nerijs Pixel Art XL LoRA)
over its HTTP API. Free and spammable — the property Stage-2 fan-out needs — and
crisper than gpt-image's downscale, which is why sprites route here and the
generalist (gpt-image-1.5) keeps backgrounds/UI. See README §Providers.

The load-bearing gap this module closes: **SDXL output has no native alpha** —
it paints the subject on a solid background with a drop shadow. So the workflow
ends in a `rembg` background-removal node (custom node
`Jcd1230/rembg-comfyui-node`, class `Image Remove Background (rembg)`), which
returns a 4-channel RGBA image ComfyUI's `SaveImage` writes as a transparent
PNG. The provider hands that raw RGBA to the runner, whose existing `postprocess`
does the nearest-neighbor downscale + palette-snap.

Like `openai_image`, the HTTP client is injectable (`client=None` lazily builds a
real `ComfyUIClient`), so offline tests mock the whole round-trip and the gate
never needs a live ComfyUI server. SDXL is trained at ~1MP, so — same shape as
the OpenAI provider — we generate at a valid SDXL bucket near the spec's aspect
ratio and let `postprocess` downscale to `spec.size`.

Runbook (dev box): launch the server headless with
`~/ComfyUI/.venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188`;
models live at `~/ComfyUI/models/checkpoints/` and `~/ComfyUI/models/loras/`.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from PIL import Image

from ..manifest import AssetSpec
from . import GenerationRequest, GenerationResult, compile_prompt

CHECKPOINT = "sd_xl_base_1.0.safetensors"
LORA = "pixel-art-xl.safetensors"
# The rembg custom node's class_type (Jcd1230/rembg-comfyui-node). Returns a
# 4-channel RGBA IMAGE, so the downstream SaveImage writes a transparent PNG.
REMBG_NODE = "Image Remove Background (rembg)"

# Steers SDXL away from the smooth/photographic modes the LoRA is fighting; the
# pixel-art *positive* cues come from the style bible via compile_prompt.
DEFAULT_NEGATIVE = (
    "3d render, photorealistic, photograph, blurry, smooth shading, "
    "anti-aliasing, gradient, depth of field, jpeg artifacts, watermark, "
    "signature, text, extra limbs, deformed"
)

# SDXL's ~1MP training buckets. We pick by aspect ratio; postprocess then
# nearest-neighbor downscales to the real (small) spec size.
GEN_SIZE_SQUARE = (1024, 1024)
GEN_SIZE_PORTRAIT = (832, 1216)
GEN_SIZE_LANDSCAPE = (1216, 832)


def choose_gen_size(spec_size: tuple[int, int]) -> tuple[int, int]:
    """Pick the SDXL bucket whose aspect ratio best matches the spec, so the
    nearest-neighbor downscale in postprocess doesn't distort proportions."""
    w, h = spec_size
    ratio = w / h
    if ratio >= 1.25:
        return GEN_SIZE_LANDSCAPE
    if ratio <= 0.8:
        return GEN_SIZE_PORTRAIT
    return GEN_SIZE_SQUARE


def seed_for(asset_id: str, attempt: int) -> int:
    """A deterministic 32-bit seed per (asset, attempt): reproducible provenance,
    yet a genuinely different roll on each retry (attempt is in the digest)."""
    digest = hashlib.sha256(f"{asset_id}:{attempt}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def build_workflow(
    *,
    positive: str,
    negative: str,
    width: int,
    height: int,
    seed: int,
    steps: int,
    cfg: float,
    sampler: str,
    scheduler: str,
    checkpoint: str = CHECKPOINT,
    lora: str = LORA,
    lora_strength: float = 1.0,
    filename_prefix: str = "dreamer_local_sd",
) -> dict:
    """The ComfyUI *API-format* graph: SDXL checkpoint -> Pixel Art XL LoRA ->
    prompt encode -> KSampler -> VAE decode -> rembg -> SaveImage. Node ids are
    stable strings; edges are `[node_id, output_index]`. Prompt/size/seed are the
    injected fields — everything else is fixed pipeline structure."""
    return {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint},
        },
        "5": {
            "class_type": "LoraLoader",
            "inputs": {
                "model": ["4", 0],
                "clip": ["4", 1],
                "lora_name": lora,
                "strength_model": lora_strength,
                "strength_clip": lora_strength,
            },
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive, "clip": ["5", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["5", 1]},
        },
        "8": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["5", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": sampler,
                "scheduler": scheduler,
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["8", 0],
                "denoise": 1.0,
            },
        },
        "10": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        # The alpha step: strips SDXL's solid background + drop shadow -> RGBA.
        "11": {
            "class_type": REMBG_NODE,
            "inputs": {"image": ["10", 0]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["11", 0], "filename_prefix": filename_prefix},
        },
    }


class ComfyUIClient:
    """Thin urllib transport for one ComfyUI generation (zero extra deps).

    `run_workflow` queues a graph (`POST /prompt`), polls `GET /history/{id}`
    until the job finishes, then fetches the produced image (`GET /view`). Kept
    behind the provider's injectable seam so the gate never touches HTTP."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8188,
        *,
        job_timeout: float = 300.0,
        request_timeout: float = 30.0,
        poll_interval: float = 1.5,
    ):
        self._base = f"http://{host}:{port}"
        self._job_timeout = job_timeout
        self._request_timeout = request_timeout
        self._poll_interval = poll_interval
        self._client_id = uuid.uuid4().hex

    def run_workflow(self, workflow: dict) -> Image.Image:
        prompt_id = self._queue(workflow)
        outputs = self._await_outputs(prompt_id)
        return self._first_image(outputs)

    def _queue(self, workflow: dict) -> str:
        body = json.dumps({"prompt": workflow, "client_id": self._client_id}).encode()
        req = urllib.request.Request(
            f"{self._base}/prompt",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._request_timeout) as resp:
                return json.load(resp)["prompt_id"]
        except urllib.error.HTTPError as e:  # 400 = graph validation failed
            detail = e.read().decode(errors="replace")
            raise RuntimeError(f"ComfyUI rejected the workflow (HTTP {e.code}): {detail}") from e

    def _await_outputs(self, prompt_id: str) -> dict:
        deadline = time.monotonic() + self._job_timeout
        url = f"{self._base}/history/{prompt_id}"
        while time.monotonic() < deadline:
            with urllib.request.urlopen(url, timeout=self._request_timeout) as resp:
                entry = json.load(resp).get(prompt_id)
            if entry:
                status = entry.get("status", {})
                if status.get("status_str") == "error":
                    raise RuntimeError(f"ComfyUI execution failed: {json.dumps(status)}")
                if entry.get("outputs"):
                    return entry["outputs"]
            time.sleep(self._poll_interval)
        raise TimeoutError(
            f"ComfyUI did not finish prompt {prompt_id} within {self._job_timeout:.0f}s"
        )

    def _first_image(self, outputs: dict) -> Image.Image:
        for node_output in outputs.values():
            for image_ref in node_output.get("images", []):
                return self._fetch_image(image_ref)
        raise RuntimeError("ComfyUI job finished but produced no image output")

    def _fetch_image(self, image_ref: dict) -> Image.Image:
        query = urllib.parse.urlencode(
            {
                "filename": image_ref["filename"],
                "subfolder": image_ref.get("subfolder", ""),
                "type": image_ref.get("type", "output"),
            }
        )
        with urllib.request.urlopen(f"{self._base}/view?{query}", timeout=self._request_timeout) as resp:
            return Image.open(io.BytesIO(resp.read()))


class LocalSDProvider:
    """Provider backed by a local ComfyUI (SDXL + Pixel Art XL + rembg).

    `client` is injectable for tests; left None it lazily builds a real
    `ComfyUIClient` pointed at host:port. The generation knobs (steps/cfg/
    sampler/scheduler) are constructor args so a lab can tune without touching
    the graph."""

    def __init__(
        self,
        client: ComfyUIClient | None = None,
        *,
        host: str = "127.0.0.1",
        port: int = 8188,
        checkpoint: str = CHECKPOINT,
        lora: str = LORA,
        lora_strength: float = 1.0,
        steps: int = 25,
        cfg: float = 7.0,
        sampler: str = "euler",
        scheduler: str = "normal",
        negative_prompt: str = DEFAULT_NEGATIVE,
        timeout: float = 300.0,
    ):
        self._client = client
        self.name = "local_sd"
        self._host = host
        self._port = port
        self.checkpoint = checkpoint
        self.lora = lora
        self.lora_strength = lora_strength
        self.steps = steps
        self.cfg = cfg
        self.sampler = sampler
        self.scheduler = scheduler
        self.negative_prompt = negative_prompt
        self._timeout = timeout

    def _client_or_default(self) -> ComfyUIClient:
        if self._client is None:
            self._client = ComfyUIClient(self._host, self._port, job_timeout=self._timeout)
        return self._client

    def generate(self, request: GenerationRequest) -> GenerationResult:
        prompt = compile_prompt(request.spec, request.bible, request.feedback)
        width, height = choose_gen_size(request.spec.size)
        seed = seed_for(request.spec.id, request.attempt)
        workflow = build_workflow(
            positive=prompt,
            negative=self.negative_prompt,
            width=width,
            height=height,
            seed=seed,
            steps=self.steps,
            cfg=self.cfg,
            sampler=self.sampler,
            scheduler=self.scheduler,
            checkpoint=self.checkpoint,
            lora=self.lora,
            lora_strength=self.lora_strength,
        )
        image = self._client_or_default().run_workflow(workflow)
        return GenerationResult(
            image=image.convert("RGBA"),
            provider=self.name,
            prompt=prompt,
            meta={
                "checkpoint": self.checkpoint,
                "lora": self.lora,
                "lora_strength": self.lora_strength,
                "gen_size": f"{width}x{height}",
                "seed": seed,
                "steps": self.steps,
                "cfg": self.cfg,
                "sampler": self.sampler,
                "scheduler": self.scheduler,
                "background_removal": "rembg",
            },
        )
