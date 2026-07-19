# Dreamer

Dreamer is an agentic system that automates game development end-to-end: from a game design document (GDD) to a final playable product. It is bigger than any single game — it is the orchestrator and harness that develops games, tested against real game projects (**labs**), and it grows by distilling what works in the labs into reusable, transferable skills.

Engine target: Godot. It's the most agent-automatable engine — `.tscn`/`.tres`/`.gd` are human-readable text, GDScript is easy to generate and statically check, `godot --headless` runs the game and imports assets from the CLI, and the scene/resource model is fully data-driven.

## Repository map

- `README.md` — this file: vision, operating model, architecture, stack (slow-changing).
- `PLAN.md` — roadmap and statuses (moves with every working session).
- `CLAUDE.md` — how we develop here: the working agreement and conventions.
- `skills/` — the skill library: one directory per skill, `skills/<name>/{knowledge,prompt}.md`.
- `packages/` — uv **workspace** members (dreamer is a monorepo; the repo root is a virtual workspace root). First member: `packages/asset-pipeline/` — dreamer's first product code, an isolated black-box package with its own `pyproject.toml`, tests, and README (see §5); gated workspace-wide by `tools/check.sh`.
- Labs are **sibling repos** (e.g. `../new-game/` — lab #1), each with its own plan and conventions.

## The core insight: it's a feedback loop, not a generator

Most attempts at this kind of automation fail for one reason: generation runs open-loop. An agent writes scenes, scripts, and assets, but never *sees* the result, so errors compound silently until the output is unsalvageable. The single most load-bearing piece of the system is not the part that writes the game — it's the part that lets agents **run the game and observe what happened**. Everything is arranged around that loop: act → observe → judge → correct.

**This is no longer a hypothesis.** The verification leg was built and battle-tested in lab #1 before dreamer existed — including a regression gate that caught a real week-old balance regression on its literal first run. The companion meta-principle, proven the hard way: *for automation, the evaluation system is the product.* Every system you can measure is a system an agent can safely change.

## The operating model: labs → skills → orchestrator

**Labs.** Real games, built for real, where each leg of automated game dev gets figured out hands-on first. Labs are disposable in principle but real enough to bite — they expose the landmines that no amount of armchair design would find (e.g. `Engine.time_scale` silently breaking `Area2D` collisions). Current labs:

- **`../new-game/`** — lab #1: a 5-wave top-down arena survival roguelite, built via agent-driven milestone commits. Home of the proven difficulty harness + regression gate. Its `AUTOMATION_PLAN.md` tracks the next legs (milestone loop, visual eval, closed-loop tuning, π_human).
- More labs soon — different genres/shapes, so skills generalize instead of overfitting to one game.

**Skills (the distillation loop).** When a leg is proven in a lab, it gets distilled into a two-file pair: a **knowledge base** (the *why*, confidence-labeled PROVEN/PARTIAL/INTENT) plus an **operating-procedure prompt** (the *how*, feedable to a fresh agent on any new game). The pair is a transferable skill — weeks of hands-on work compressed into something re-executable in a session. First member of the library, already proven:

- `skills/evaluation/knowledge.md` + `skills/evaluation/prompt.md` — the evaluation & verification leg: policy-relative difficulty measurement (bot ladder, seeded Monte-Carlo, observer node, `--fixed-fps` lossless speedup, meta-loop modeled via the game's real APIs) frozen into a regression gate with banded assertions.

Future skills follow the same path: build concretely in a lab → distill knowledge + procedure → library grows. Candidates: GDD compilation, milestone build loop, visual evaluation, asset pipeline, closed-loop tuning.

**Orchestrator.** Dreamer's own product: the system that takes a GDD and drives a game to completion by applying the skill library — dispatching specialized agents, tracking state, running gates, escalating to the human at taste checkpoints. We build the orchestrator here and test it in the labs.

## Core parts of the system

Status: ✅ proven in a lab · ◐ partially proven · ☐ open.

### 1. Spec layer — GDD compilation ☐

A GDD is a wish, not a spec: ambiguous, incomplete, often self-contradictory. The first transformation is compiling prose into a formal intermediate representation (IR) — mechanics as rules/state machines, entity and content inventories, scene/UI flow graphs, progression curves, an art direction document. The IR is what every downstream agent consumes, and it's what makes *incremental* development possible: when the design changes, diff the IR and rebuild only the affected subgraph. Needs an ambiguity-resolution loop — escalate questions or make assumptions and log them explicitly. (Lab #1's `GAME_DESIGN.md`/`PROTOTYPE_PLAN.md` were hand-authored; this layer is untouched.)

### 2. Orchestrator — a build system for game dev ◐

The IR gets decomposed into a dependency-ordered task graph dispatched to specialized agents (gameplay code, level/content, art, audio, UI). Mental model: a build system — targets, dependencies, caching, invalidation, re-planning when verification fails. The pipeline is **milestone-shaped, not waterfall-shaped**: playable graybox core loop first, then content, then art and polish passes. Lab #1's entire git history is this loop run manually (human-driven agent sessions, one milestone per commit, gate-green as the hand-back criterion) — `AUTOMATION_PLAN.md` Phase 2 turns it into a command. That milestone loop is the seed of the orchestrator.

### 3. Engine harness ◐

The tool API agents use to act on Godot: create/edit scenes and scripts, wire signals, configure project settings, manage imports. Direct text-file manipulation plus headless CLI covers most of it (proven daily in lab #1); known sharp edges are documented (class-cache reimports, autoload resolution in headless scripts). An MCP-style wrapper may come later if direct manipulation stops scaling.

### 4. Observation & verification ✅ (logic/balance) · ☐ (visual)

The proven half: script/scene/resource load checks, boot checks, unit tests over the meta-loop math through real APIs, and the difficulty harness — bot policy ladder, deterministic seeded Monte-Carlo, difficulty fingerprint (lethality, accumulation, agency, economy flow), all frozen into a one-command regression gate with banded assertions and physics-sanity tripwires. Bands move only in deliberate retune commits; a band failure is a real regression, never a flake.

The open half: **visual evaluation** — screenshot harness reviewed by vision against per-scene checklists, and UI-bot flow tests walking the real menu graph. This is lab #1's Phase 3 and the prototype of the art-evaluation leg.

### 5. Asset pipeline ◐

Image/audio generation is the easy half; the hard half is **consistency** — generation tools are stateless but a game needs one coherent style. It's an **isolated package (`packages/asset-pipeline/`, a member of dreamer's uv workspace) with its own `pyproject.toml`, tests, and README, treated as a black box**: asset requests in, checked assets out; the orchestrator asks for art without knowing anything about image generation. The design decisions (2026-07-02, provider choice updated 2026-07-04):

- **Claude is the eyes, never the hands.** Anthropic models don't generate images; Claude's roles are orchestration, style-bible/prompt compilation, and vision QA. Pixel generation is provider-pluggable.
- **Deterministic-first hierarchy:** every measurable property (palette conformance, alpha, dimensions, grid) is a code assert in the gate; vision judges only the residue (style match, silhouette readability); regeneration is the last resort.
- **Structured contract, not an open prompt.** The box's front door is `Studio.produce(manifest, bible) -> report` — structured `AssetSpec`s in, checkable results out. Free-form prompts live *inside* (prompt compilation is an implementation detail); an open natural-language interface would defeat the deterministic gate. Provider selection and per-class routing are hidden behind the facade — the caller never constructs a provider.
- **Providers per asset class:** a **local SDXL + Pixel Art XL LoRA specialist** for pixel-art sprites & animation — installed and proven on the dev box (2026-07-04), free + spammable (what Stage-2 fan-out needs) and crisper than a downscale; OpenAI `gpt-image-1.5` as the general-2D generalist for backgrounds/UI/large assets (native transparent background — its successor `gpt-image-2` is stronger on text/resolution but *dropped* transparency support, so it's unusable for cutout assets; `gpt-image-1.5` keeps alpha and is the current pin); Grok Imagine deferred until fan-out variant generation makes its per-image price matter. **This reverses the earlier plan** of hosted specialists (Retro Diffusion / PixelLab) with "local only if scale demands" — local is now the specialist of record.

Built (offline core, `packages/asset-pipeline/`, tested but unproven in a lab): versioned style bible + asset manifest/ledger schemas, deterministic post-processing (nearest-neighbor scale, palette quantization, alpha snap), check suite, provider protocol with a local-file provider, bounded regenerate-with-feedback runner, a stubbed vision-judge interface for the visual-eval leg to fill, and the `Studio` facade that seals all of this behind the public boundary. Also built: the first live provider (`gpt-image-1.5`, transparency-aware, generated at a valid API size then downscaled) and Godot pixel-art `.import` sidecars — both offline-tested but not yet exercised against the real API or inside Godot. Open: the local SDXL specialist provider (`local_sd.py` + rembg alpha step), real vision QA, per-class routing, audio, lab proof.

### 6. Project memory & ledger ◐

Durable state beyond git: decisions made, conventions established, assumptions logged, what's verified vs. merely written. Lab #1's working pattern — `CLAUDE.md` conventions + `AUTOMATION_PLAN.md` phase statuses + structured commits — is a manual version; dreamer formalizes it so any session (or agent) picks up where the last left off.

### 7. Human checkpoints ◐

Cheap, well-placed gates: approve the formalized spec, approve the art direction, approve the vertical slice. Automation between gates, judgment at them. The target division of labor, validated in lab #1: **the human is a sparse taste-oracle, not the regression detector.** Escalation when an agent fails repeatedly or hits genuine ambiguity.

### 8. Playability evaluation ◐

"Compiles and doesn't crash" is necessary; games also need to be *fun*. Proven core: fun operationalized as *difficulty, measured against the intended player's skill, landing in a target band* (the flow channel) — measurable, tunable, assertable. Open frontier: pacing metrics (the "hard but boring" guard), closed-loop auto-tuning ("tune X to target Y" as one command), and π_human — fitting a policy to real play traces so difficulty becomes a personal fun proxy.

## Stack

Promote what the lab proved; add exactly one new layer (the orchestrator), in two stages.

- **Engine:** Godot 4.6 — GDScript + text resources, driven via `godot --headless`. Per-game tooling (harness, gate scripts) stays GDScript inside each lab; nothing dreamer-side reimplements game logic.
- **Verification:** bash + Python (the `check.sh` + assert-script pattern). Exit codes are the contract every layer above depends on.
- **Skills:** markdown, runtime-agnostic — they must outlive any orchestrator version that feeds them.
- **Orchestration, staged:**
  - *Stage 1 (now):* Claude Code itself — skills/commands/hooks in the lab repos; the `/milestone` loop is just a command. Zero new infrastructure; running it human-triggered teaches us what the real orchestrator must handle.
  - *Stage 2 (when loops run unattended or fan out):* Python + the Claude Agent SDK — sessions spawned programmatically, gate as the brake, budgets, resumability, parallel fan-out over variants compared via the deterministic harness.
  - No agent frameworks (LangGraph, CrewAI, …): Claude Code already is the agent harness, and dreamer's control flow is simple deterministic code.
- **Assets:** Python (`packages/asset-pipeline/`, a uv-workspace member, gated by `tools/check.sh`); image-gen APIs behind one provider-agnostic client (providers churn; the style-bible threading and post-processing are the durable parts).
- **State:** git + markdown ledgers in-repo; JSON for machine outputs. No database until fan-out volumes force one.

## Scope decisions

- **2D, game-jam scale** for v1. Dramatically more tractable for asset generation and visual verification; lab #1 already fits this shape.
- Later: **fan-out agentic workflows** — generate multiple candidate interpretations/variants (designs, art directions, tunings) in parallel and select, rather than committing to one path. The deterministic harness makes candidates *comparable*, which is what makes fan-out meaningful.
- We need to start somewhere; depth first, breadth later.

## Status & roadmap

Lives in [`PLAN.md`](PLAN.md) — skill library, orchestrator stages, labs, and the near-term sequence. How we work day-to-day is in [`CLAUDE.md`](CLAUDE.md).
