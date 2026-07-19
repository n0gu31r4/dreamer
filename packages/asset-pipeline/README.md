# asset_pipeline — the art black box

Dreamer's asset pipeline is an **isolated package with one job**: turn a game's
asset requests into checked, game-ready 2D assets. It hides *how* — which model
makes which sprite, prompt wording, post-processing, retries — behind a single
front door so the orchestrator can ask for art without knowing anything about
image generation.

> Confidence labels (repo convention): ✅ PROVEN in a lab · ◐ built, unproven · ☐ INTENT (not built).

## The boundary (what callers touch) ◐

Callers import from `asset_pipeline` **only**. The public surface is small:

```python
from asset_pipeline import Studio, StyleBible, Manifest, AssetSpec

bible = StyleBible.load("style.json")        # the art-direction contract (palette, grid, bg policy)
manifest = Manifest.load("assets.json")      # what the game needs: a list of AssetSpec
studio = Studio.default("openai")            # pick a generator; caller never imports a provider
report = studio.produce(manifest, bible, out_dir="assets/")
#   -> ProductionReport(passed=N, failed=M); manifest updated in place with full provenance
```

**The contract, precisely:**

- **In:** a `StyleBible` (shared style state — the consistency weapon) + a `Manifest` of `AssetSpec`s (`id`, `category`, `size`, `description`).
- **Out:** a `ProductionReport` (counts) + each manifest entry updated with status and provenance (prompt, checks, verdict, file). Provider errors are recorded per asset, never raised — one bad asset never sinks the batch.
- **Hidden:** provider choice + routing, prompt compilation, post-processing, the deterministic checks, the regenerate-with-feedback loop, vision QA.

**Boundary rule:** `providers/`, `postprocess`, `checks`, `qa`, `pipeline` are **internal** — subject to change without notice. The orchestrator never constructs a provider or a judge; `Studio.default(...)` does. Structured contract at the mouth; free-form prompts live *inside* (see `providers.compile_prompt`). This is deliberate: an open natural-language interface would defeat the deterministic gate, which only works because requests are structured and results are checkable against them.

## What's inside ◐

The act → observe → judge → correct loop for one asset:

```
generate (provider) -> post-process (code) -> deterministic checks (code)
    -> vision QA (judge) -> pass: save + ledger | fail: retry with feedback (bounded)
```

**Deterministic-first:** every measurable property (palette, alpha, dimensions, grid) is a code assert; the vision judge only rules on the residue (style match, silhouette readability). The judge is a no-op stub today — deterministic checks are the only real eyes in v1 until the visual-eval leg lands.

**Sizing & palette (what makes output read as pixel art).** Both these live in the caller's inputs, not the box, and they dominate perceived quality. Providers generate at ~1024px; `postprocess` then nearest-neighbor downscales to `AssetSpec.size` and snaps to the **fixed** `StyleBible.palette` (the snap is what makes palette conformance a deterministic gate). Two lessons from the 2026-07-19 smoke runs: (1) **size** — a detailed character needs ~96–128px; at 32×32 the centered, cut-out subject fills ~15px and reads as a blob. (2) **palette** — 6 colors is too few; it collapses a shaded sprite to mud at *every* size. Use a real limited palette (~16–32 colors, e.g. DawnBringer-16). The smoke scripts now demo 96×96 + DB16. (A richer *fixed* palette keeps the gate and cross-asset consistency; per-image *adaptive* palettes would look great but break both — a deferred design fork.)

## Providers per asset class

The box routes by asset class. **Routing is ◐ built** (`Studio.routed(...)` → an internal `CategoryRouter`, a `spec.category → provider` map with a default): sprites go to the `local_sd` specialist, everything else (backgrounds, UI, tilesets) to the `gpt-image` generalist. The router is itself a `Provider`, so the pipeline is unchanged and the concrete generator lands in each asset's provenance. `Studio.default(name)` still drives a single provider.

| Provider | Role | Status |
|---|---|---|
| **local SDXL + Pixel Art XL** (`local_sd`) | pixel-art **specialist**: sprites, characters, animation | ◐ built + wired + run live (clean rembg alpha, all checks pass); sprite-scale quality tuning open — see below |
| **OpenAI `gpt-image-1.5`** (`openai`) | **generalist**: backgrounds, UI, large assets; native alpha | ◐ built + exercised live (real sprite passed all deterministic checks 2026-07-19) |
| **local-file** (`local`) | reads pre-made PNGs; offline, tests, hand-drawn assets | ✅ used by the gate |

Why local SDXL is the specialist (decision 2026-07-04): it is **free + spammable** — exactly what Stage-2 fan-out needs — and produces crisper pixel art than gpt-image's downscale. `gpt-image-1.5` stays the generalist for big/one-off assets. This reverses the earlier "hosted specialists (Retro Diffusion / PixelLab); local only if scale demands" plan. Grok Imagine remains deferred until fan-out makes its per-image price matter.

## Local SDXL specialist — setup (runbook) ◐ wired in

Now a real provider (`providers/local_sd.py`, 2026-07-19): a stdlib-`urllib` ComfyUI client (`POST /prompt` → poll `GET /history/{id}` → `GET /view`) driving an SDXL + Pixel Art XL + rembg graph. Injectable client, so the gate mocks the whole round-trip offline. First live run passed all deterministic checks with a clean transparent cutout. **Caveat:** at 32×32 through the generic-palette pipeline the output reads dark/silhouette-y — the "crisper pixel art" advantage (from the 2026-07-04 isolated test at native scale) isn't yet confirmed at sprite scale; palette / target-size / LoRA-strength tuning is the open follow-up (a human taste call).

- **ComfyUI** 0.27 at `~/ComfyUI`, on a **uv-managed** Python 3.12 venv. (System python 3.12 lacks `Python.h`, which breaks ComfyUI's Triton JIT at import; the uv standalone python bundles the headers — no sudo / `python3-dev`.)
- **Models:** `~/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors` + `~/ComfyUI/models/loras/pixel-art-xl.safetensors` (nerijs Pixel Art XL LoRA, strength 1.0).
- **Launch headless:** `~/ComfyUI/.venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188` → API on `localhost:8188`.
- **The alpha step (gap now closed):** SDXL paints the subject on a **solid background with a drop shadow — no native alpha.** The workflow ends in a `rembg` node (custom node `Jcd1230/rembg-comfyui-node`, class `Image Remove Background (rembg)`) that returns a 4-channel RGBA image `SaveImage` writes with transparency; the runner's existing `postprocess` then does the downscale + palette-snap. **Install once:** `git clone https://github.com/Jcd1230/rembg-comfyui-node ~/ComfyUI/custom_nodes/rembg-comfyui-node` then `uv pip install --python ~/ComfyUI/.venv/bin/python rembg onnxruntime` and restart ComfyUI. (u2net weights, ~176 MB, auto-download to `~/.u2net/` on first use.)
- **Smoke it (free, no key):** with the server up, from the workspace root
  `uv run --package asset-pipeline python packages/asset-pipeline/scripts/smoke_local.py` — one sprite end-to-end, PNG + `.import` sidecar into `_smoke_out/` (gitignored).

## Secrets

`gpt-image-1.5` needs `OPENAI_API_KEY`, kept in the **workspace-root** `.env` (gitignored). The gate never touches the live API — it's exercised only via `scripts/smoke_live.py`. To run it, from the workspace root:

```bash
set -a; . ./.env; set +a
uv run --package asset-pipeline --extra live python packages/asset-pipeline/scripts/smoke_live.py
```

## Status

See `../../PLAN.md` (Dreamer code → asset pipeline) for milestone tracking. Short version: offline core + boundary facade built and tested; both live providers (`gpt-image-1.5` generalist, `local_sd` SDXL specialist with rembg alpha) exercised live and passing the deterministic checks; per-class routing built. Open: sprite-scale quality tuning (taste call), in-Godot import verification (no engine here), real vision QA, and lab proof — no lab has consumed the pipeline yet.
