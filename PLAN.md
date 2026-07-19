# PLAN.md — dreamer roadmap & statuses

Dreamer-level tracking only. Each lab keeps its own plan (lab #1: `../new-game/AUTOMATION_PLAN.md`); this file tracks the meta-level: the skill library, the orchestrator, the labs, and the trials. Statuses move **in the commit that does the work**.

Status legend: ☐ planned · ◐ in progress / drafted-unproven · ☑ done

## Skill library (`skills/<name>/{knowledge,prompt}.md`)

| Skill | Status | Evidence base | Notes |
|---|---|---|---|
| `evaluation` | ☑ distilled | new-game (built & battle-tested) | Measurement harness + regression gate. Core PROVEN; visual/pacing/π_human parts still INTENT. |
| `gdd` | ◐ drafted, unproven | new-game's GDD reviewed against its build history | Template + decision-status vocabulary (LOCKED/TUNABLE/OPEN/DEFERRED) + HITL co-authoring procedure. Cold-tested by trial #1. |
| `bootstrap` | ◐ drafted, unproven | new-game's ~24-commit history + doc trio | The from-zero master procedure: scaffold → doc trio → milestone loop → eval leg → prototype. Cold-tested by trial #1. |
| `milestone-loop` | ☐ | — | Currently inline as bootstrap Phase 2. Distill into its own skill (and a `/milestone` command) after trial #1 grades it. |
| `visual-eval` | ☐ | new-game (Phase 3, not built) | Screenshot harness + vision review; UI-bot flow tests. Prototype of the art-evaluation leg. |
| `asset-pipeline` | ☐ | — | Skill not distilled (needs lab proof), but **v1 offline core code exists** in `packages/asset-pipeline/` — pulled forward 2026-07-02 by human decision (see Dreamer code below). Vision-QA slot stubbed; "eyes before art" satisfied by deterministic checks until visual-eval lands. |

## Dreamer code (uv workspace; members under `packages/`, gate: `tools/check.sh`)

- ◐ **Milestone 1 — offline core** (2026-07-02): style-bible + manifest/ledger schemas, deterministic post-processing (NN scale, palette quantize, alpha snap), check suite (dimensions, transparency, palette, grid), provider protocol + local-file provider, bounded regenerate-with-feedback runner, stubbed vision-judge interface. 35 tests, gate green. Drafted-unproven: no lab has consumed it yet.
- ◐ **Milestone 2 — first live provider** (2026-07-03; **live path proven 2026-07-19**): OpenAI `gpt-image-1.5` provider (native alpha; **1.5 not `gpt-image-2`** — 2 dropped transparency support; 1.5 chosen over the plan's original `gpt-image-1` because it keeps alpha *and* is newer/better) + Godot pixel-art `.import` sidecars (`godot_import.py`) + `--live` smoke script (`scripts/smoke_live.py`, excluded from gate; needs `--extra live` + `OPENAI_API_KEY`). 48 tests, gate green. **Live API call now exercised** (`smoke_live.py`, real key): one `sprite` ran generate → postprocess → checks → stub judge and **passed all deterministic checks** (32×32 RGBA, 100% transparent border, all pixels on the 6-color palette); the `.import` sidecar wrote correctly. Confirms the muddy-downscale tradeoff — gpt-image at 1024→32 is soft-edged, not pixel-native, which is exactly why the local SDXL specialist (M3) exists. **Still ☐:** true in-Godot import (`godot --headless --import`) — no engine on this box, so the sidecar's actual acceptance by Godot 4 remains unverified; sidecar *content* is asserted in the gate.
- ◐ **Milestone 3 kickoff — black-box the package + make it a workspace member** (2026-07-19): the repo is now a **uv workspace (monorepo)** — virtual root `pyproject.toml` (`[tool.uv.workspace] members=["packages/*"]` + shared `dev` dependency-group), first member `packages/asset-pipeline/` (src layout: `src/asset_pipeline/`) with its own `pyproject.toml`, `tests/`, `scripts/`, and README. Code boundary: `Studio` facade (`studio.py`) is the single public front door — structured contract in (`StyleBible` + `Manifest`), `ProductionReport` out; provider + judge construction hidden behind `Studio.default(...)`. `asset_pipeline/__init__.py` declares the public surface via `__all__`; everything else (`providers`, `postprocess`, `checks`, `qa`, `pipeline`) is internal. `packages/asset-pipeline/README.md` is the package front door (contract + provider-routing map + local-SD runbook). Gate now `uv sync --all-packages` + pytest; 51 tests green. **Recorded the 2026-07-04 provider decision** (local SDXL + Pixel Art XL LoRA is the pixel-art specialist — free + spammable for fan-out; reverses the hosted Retro Diffusion / PixelLab plan).
- ◐ **Milestone 3 — local SDXL specialist provider wired + routing** (2026-07-19): `providers/local_sd.py` — a stdlib-`urllib` ComfyUI client (`POST /prompt` → poll `GET /history/{id}` → `GET /view`) driving an SDXL base + Pixel Art XL LoRA graph that **ends in a `rembg` node** (custom node `Jcd1230/rembg-comfyui-node`) to supply the alpha SDXL lacks; injectable client so the gate mocks the round-trip offline. Per-class routing built: `Studio.routed(...)` → an internal `CategoryRouter` (sprites→`local_sd`, else→`gpt-image`), a plain category map, pipeline unchanged; the concrete generator now lands in each attempt's provenance. 60 tests, gate green. **Run live** (`scripts/smoke_local.py`, excluded from gate): one real sprite went generate→rembg→postprocess→checks and **passed all deterministic checks** with a clean transparent cutout; `.import` sidecar written. **Still ☐ / escalated to the human:** sprite-scale quality — at 32×32 through the generic-palette pipeline the specialist reads dark/silhouette-y, so the "crisper than gpt-image" claim is *not yet visually confirmed at sprite scale* (needs a taste call + palette/target-size/LoRA-strength tuning). Also still ☐: real vision QA, in-Godot import verification (no engine here), lab proof.
- ☐ **Lab proof**: run the pipeline against a real lab's GDD; only then distill `skills/asset-pipeline/`.

## Orchestrator

- ◐ **Stage 1 — Claude Code native.** The pipeline IS the skill prompts, human-launched: `gdd/prompt.md` (step 0, HITL) → `bootstrap/prompt.md` (scaffold + milestone loop + eval handoff). Drafted; trial #1 is its first execution.
- ☐ **Stage 2 — Python + Claude Agent SDK.** Sessions spawned programmatically, budgets, resumability, fan-out over variants compared via the deterministic harness. Only after Stage 1's trials teach us what it must handle.

## Labs & trials

- ◐ **Lab #1 — `../new-game/`** (top-down arena survival roguelite). Built interactively (human + Opus); harness + gate live here. New role since 2026-06-12: **the control** — the human+agent-built baseline that automated builds are graded against — and host for mature-game legs (visual eval, closed-loop tuning, π_human; see its `AUTOMATION_PLAN.md`).
- ☐ **Trial #1 — replicate new-game from its own GDD.** Fresh sibling repo; inputs = new-game's `GAME_DESIGN.md` + dreamer skills, **no peeking at the control**. Tests, in one run: the GDD template's sufficiency, cold re-execution of the evaluation skill, and the bootstrap procedure end to end. Graded against the control: milestones reached, escalations, doc quality, divergence, cost.
- ☐ **Lab #2 — new genre.** After trial #1: a different game shape from a *new* GDD (authored via `skills/gdd/prompt.md`), to force generalization beyond the roguelite.

## Near-term sequence

1. ☑ ~~Draft the kickstart machinery~~ — `skills/gdd/` + `skills/bootstrap/` (2026-06-12).
1b. ☑ ~~Asset-pipeline milestone 1 (offline core)~~ — pulled forward by human decision (2026-07-02); parallel track, does not displace trial #1 as the next dreamer-level step.
2. **Pre-trial check on the GDD input** — run new-game's `GAME_DESIGN.md` through the conformance check; fix the input (notably the missing §10 difficulty-intent section), not the game.
3. **Trial #1** — fresh repo, clean context, run the bootstrap. Human plays taste-oracle per the procedure; grade afterwards against the control.
4. **Post-trial distillation** — fold lessons into the skills; promote ◐ labels that survived; distill `milestone-loop` standalone.
5. **Visual eval leg** (host: whichever lab fits) → `skills/visual-eval/`.

## Standing rules

- Skills are distilled **from lab evidence** — observed-once material ships labeled ◐/unproven, never as PROVEN; promotion requires a cold re-execution (a trial).
- Scope guard: 2D, jam-scale, depth-first (one leg at a time) until the orchestrator exists.
- Replication trials never read their control.
