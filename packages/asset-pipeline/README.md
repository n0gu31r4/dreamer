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

## Providers per asset class

The box routes by asset class. **Routing itself is ☐ INTENT** — today a `Studio` runs one configured provider for all assets; per-class routing arrives when the second real generator (`local_sd`) does.

| Provider | Role | Status |
|---|---|---|
| **local SDXL + Pixel Art XL** (`local_sd`) | pixel-art **specialist**: sprites, characters, animation | ☐ built on the box, not wired in — see below |
| **OpenAI `gpt-image-1.5`** (`openai`) | **generalist**: backgrounds, UI, large assets; native alpha | ◐ live provider built, not yet exercised against the real API |
| **local-file** (`local`) | reads pre-made PNGs; offline, tests, hand-drawn assets | ✅ used by the gate |

Why local SDXL is the specialist (decision 2026-07-04): it is **free + spammable** — exactly what Stage-2 fan-out needs — and produces crisper pixel art than gpt-image's downscale. `gpt-image-1.5` stays the generalist for big/one-off assets. This reverses the earlier "hosted specialists (Retro Diffusion / PixelLab); local only if scale demands" plan. Grok Imagine remains deferred until fan-out makes its per-image price matter.

## Local SDXL specialist — setup (runbook) ☐ not wired in

Installed and proven **in isolation** on the dev box (2026-07-04): produced a crisp, readable pixel goblin in ~10s at $0. **Not yet a provider** — there is no `providers/local_sd.py`. This section is the runbook for building it.

- **ComfyUI** 0.27 at `~/ComfyUI`, on a **uv-managed** Python 3.12 venv. (System python 3.12 lacks `Python.h`, which breaks ComfyUI's Triton JIT at import; the uv standalone python bundles the headers — no sudo / `python3-dev`.)
- **Models:** `~/ComfyUI/models/checkpoints/sd_xl_base_1.0.safetensors` + `~/ComfyUI/models/loras/pixel-art-xl.safetensors` (nerijs Pixel Art XL LoRA, strength 1.0).
- **Launch headless:** `~/ComfyUI/.venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188` → API on `localhost:8188`.
- **Open gap before it's a real provider:** SDXL output is a **solid background with a drop shadow — no native alpha.** `local_sd.py` needs a background-removal step (ComfyUI `rembg`/RMBG node) to yield transparent sprites, *then* hand off to the existing `postprocess` (downscale + palette-snap).

## Secrets

`gpt-image-1.5` needs `OPENAI_API_KEY`, kept in the **workspace-root** `.env` (gitignored). The gate never touches the live API — it's exercised only via `scripts/smoke_live.py`. To run it, from the workspace root:

```bash
set -a; . ./.env; set +a
uv run --package asset-pipeline --extra live python packages/asset-pipeline/scripts/smoke_live.py
```

## Status

See `../../PLAN.md` (Dreamer code → asset pipeline) for milestone tracking. Short version: offline core + boundary facade built and tested; live OpenAI path and Godot import built but unexercised; the local SDXL provider is the next build (Milestone 3); no lab has consumed the pipeline yet.
