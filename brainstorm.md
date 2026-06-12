# Dreamer — Brainstorm

Dreamer is an agentic system that automates game development end-to-end: from a game design document (GDD) to a final playable product. It is bigger than any single game — it is the orchestrator and harness that develops games, tested against real game projects (**labs**), and it grows by distilling what works in the labs into reusable, transferable skills.

Engine target: Godot. It's the most agent-automatable engine — `.tscn`/`.tres`/`.gd` are human-readable text, GDScript is easy to generate and statically check, `godot --headless` runs the game and imports assets from the CLI, and the scene/resource model is fully data-driven.

## The core insight: it's a feedback loop, not a generator

Most attempts at this kind of automation fail for one reason: generation runs open-loop. An agent writes scenes, scripts, and assets, but never *sees* the result, so errors compound silently until the output is unsalvageable. The single most load-bearing piece of the system is not the part that writes the game — it's the part that lets agents **run the game and observe what happened**. Everything is arranged around that loop: act → observe → judge → correct.

**This is no longer a hypothesis.** The verification leg was built and battle-tested in lab #1 before dreamer existed (see below) — including a regression gate that caught a real week-old balance regression on its literal first run. The companion meta-principle, proven the hard way: *for automation, the evaluation system is the product.* Every system you can measure is a system an agent can safely change.

## The operating model: labs → skills → orchestrator

**Labs.** Real games, built for real, where each leg of automated game dev gets figured out hands-on first. Labs are disposable in principle but real enough to bite — they expose the landmines that no amount of armchair design would find (e.g. `Engine.time_scale` silently breaking `Area2D` collisions). Current labs:

- **`../new-game/`** — lab #1: a 5-wave top-down arena survival roguelite, built via agent-driven milestone commits. Home of the proven difficulty harness + regression gate. Its `AUTOMATION_PLAN.md` tracks the next legs (milestone loop, visual eval, closed-loop tuning, π_human).
- More labs soon — different genres/shapes, so skills generalize instead of overfitting to one game.

**Skills (the distillation loop).** When a leg is proven in a lab, it gets distilled into a two-file pair: a **knowledge base** (the *why*, confidence-labeled PROVEN/PARTIAL/INTENT) plus an **operating-procedure prompt** (the *how*, feedable to a fresh agent on any new game). The pair is a transferable skill — weeks of hands-on work compressed into something re-executable in a session. First member of the library, already proven:

- `../evaluation_system_knowledge.md` + `../evaluation_system_prompt.md` — the evaluation & verification leg: policy-relative difficulty measurement (bot ladder, seeded Monte-Carlo, observer node, `--fixed-fps` lossless speedup, meta-loop modeled via the game's real APIs) frozen into a regression gate with banded assertions.

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

### 5. Asset pipeline ☐

Image/audio generation is the easy half; the hard half is **consistency** — generation tools are stateless but a game needs one coherent style. Needs: a versioned "style bible" (palette, reference sheets, prompt fragments) threaded through every generation call; post-processing automation (background removal, sprite-sheet slicing, palette enforcement); automatic Godot import configuration; a manifest tracing spec → asset → usage.

### 6. Project memory & ledger ◐

Durable state beyond git: decisions made, conventions established, assumptions logged, what's verified vs. merely written. Lab #1's working pattern — `CLAUDE.md` conventions + `AUTOMATION_PLAN.md` phase statuses + structured commits — is a manual version; dreamer formalizes it so any session (or agent) picks up where the last left off.

### 7. Human checkpoints ◐

Cheap, well-placed gates: approve the formalized spec, approve the art direction, approve the vertical slice. Automation between gates, judgment at them. The target division of labor, validated in lab #1: **the human is a sparse taste-oracle, not the regression detector.** Escalation when an agent fails repeatedly or hits genuine ambiguity.

### 8. Playability evaluation ◐

"Compiles and doesn't crash" is necessary; games also need to be *fun*. Proven core: fun operationalized as *difficulty, measured against the intended player's skill, landing in a target band* (the flow channel) — measurable, tunable, assertable. Open frontier: pacing metrics (the "hard but boring" guard), closed-loop auto-tuning ("tune X to target Y" as one command), and π_human — fitting a policy to real play traces so difficulty becomes a personal fun proxy.

## Scope decisions

- **2D, game-jam scale** for v1. Dramatically more tractable for asset generation and visual verification; lab #1 already fits this shape.
- Later: **fan-out agentic workflows** — generate multiple candidate interpretations/variants (designs, art directions, tunings) in parallel and select, rather than committing to one path. The deterministic harness makes candidates *comparable*, which is what makes fan-out meaningful.
- We need to start somewhere; depth first, breadth later.

## Where we are, and what's next

The riskiest piece (verification) is de-risked and distilled. The natural next moves, in rough order of leverage:

1. **The milestone loop** (lab #1, Phase 2) — automate the build step that's been run manually all along; the gate gives it brakes. This is the orchestrator's first organ, built where it can be tested.
2. **Visual evaluation** (lab #1, Phase 3) — gives agents eyes; prototype of the art leg and prerequisite for the asset pipeline.
3. **Spec layer** — start small: formalize lab #1's design docs into an IR shape and see what the milestone loop actually needs from it.
4. **Lab #2** — a different genre, to force the eval skill (and everything after it) to generalize.
