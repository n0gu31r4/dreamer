# PLAN.md — dreamer roadmap & statuses

Dreamer-level tracking only. Each lab keeps its own plan (lab #1: `../new-game/AUTOMATION_PLAN.md`); this file tracks the meta-level: the skill library, the orchestrator, and the labs themselves. Statuses move **in the commit that does the work**.

Status legend: ☐ planned · ◐ in progress · ☑ done

## Skill library (`skills/<name>/{knowledge,prompt}.md`)

| Skill | Status | Source lab | Notes |
|---|---|---|---|
| `evaluation` | ☑ distilled | new-game | Measurement harness + regression gate. Core PROVEN; visual/pacing/π_human parts still INTENT in the knowledge file. |
| `milestone-loop` | ☐ | new-game (Phase 2) | Build & grade as a lab command first (experiment protocol in the lab's plan), distill once proven. |
| `visual-eval` | ☐ | new-game (Phase 3) | Screenshot harness + vision review; UI-bot flow tests. Prototype of the art-evaluation leg. |
| `spec-ir` (GDD compilation) | ☐ | — | Start by formalizing lab #1's hand-written design docs into an IR shape the milestone loop consumes. |
| `asset-pipeline` | ☐ | — | Style bible, generation client, post-processing, Godot import config. Gated on visual-eval (need eyes before art). |

## Orchestrator

- ◐ **Stage 1 — Claude Code native.** The skill library + lab commands/hooks; human-triggered. First artifact: the `/milestone` command in lab #1, run as a graded experiment (2–3 small backlog items; grade scoping, gate catches, review triviality; tighten the prompt between runs).
- ☐ **Stage 2 — Python + Claude Agent SDK.** Unattended multi-step loops, budgets, resumability, fan-out over variants compared via the deterministic harness. Only after Stage 1 has taught us what it must handle.

## Labs

- ◐ **Lab #1 — `../new-game/`** (top-down arena survival roguelite). Difficulty harness + gate built; balance leg green. Remaining legs tracked in its `AUTOMATION_PLAN.md` (gate hardening, milestone loop, visual eval, closed-loop tuning, π_human).
- ☐ **Lab #2** — different genre/shape, to force the eval skill (and everything after it) to generalize. Pick after the milestone loop works in lab #1.

## Near-term sequence

1. **`/milestone` command in lab #1** — automate the build step that's been run manually all along; the gate gives it brakes. The orchestrator's first organ, built where it can be tested.
2. **Visual evaluation leg in lab #1** — gives agents eyes; prerequisite for the asset pipeline. Distill into `skills/visual-eval/` once proven.
3. **Spec-layer experiment** — formalize lab #1's design docs into an IR; size it by what the milestone loop actually needs from it.
4. **Lab #2** — generalization pressure.

## Standing rules

- Skills are distilled **only from proven lab work** — never written speculatively.
- Scope guard: 2D, jam-scale, depth-first (one leg at a time) until the orchestrator exists.
