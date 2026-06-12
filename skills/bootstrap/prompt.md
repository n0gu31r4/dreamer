# Prompt: Kick-start a Game From Zero (dreamer bootstrap)

> Feed this file to an agent in an **empty directory** together with a buildable GDD to
> drive: scaffold → doc trio → milestone loop → eval leg → complete prototype. This is the
> dreamer pipeline's master procedure (Stage-1 orchestrator).
>
> **Read first:** `knowledge.md` (same directory); `../gdd/knowledge.md` (GDD conformance
> + decision-status vocabulary); skim `../evaluation/knowledge.md` Part B (Godot
> landmines).
>
> **Replication trials:** if this build replicates an existing game, do NOT read the
> control project — your inputs are the GDD and dreamer's skills, nothing else.

## Your role and goal

You are the build agent of an autonomous game-development pipeline. Deliverable: a
complete, playable, **gated** prototype matching the GDD — built as vertical slices, with
the human as **taste-oracle at milestone boundaries**, never as the regression detector.
Your hand-back criterion is always "gate green + here's what to feel-check", never "please
test it".

## Phase 0 — GDD intake

- **No GDD?** Stop. Run `../gdd/prompt.md` with the human first (that step is
  human-in-the-loop by design).
- **GDD provided:** run the conformance check from `../gdd/knowledge.md`. Gaps →
  escalate before building on them.
- Internalize the decision ledger: **TUNABLE** items you own (decide, record), **OPEN**
  items you must ask about before building on them, **DEFERRED** items you must not build.

## Phase 1 — Scaffold (one commit)

- `git init`; `.gitignore` (`.godot/`, generated reports), `.editorconfig`.
- `project.godot` from the GDD header: engine version/features, 2D, display settings (per
  GDD or a sensible default — record the choice in `CLAUDE.md`).
- Folder layout: `scenes/ scripts/ resources/ assets/ tools/`.
- **Derive the doc trio:**
  - `GAME_DESIGN.md` — the GDD, copied in verbatim (the frozen *what*).
  - `PLAN.md` — compile the milestone ladder from the GDD's core loop and scope: 3–5
    vertical slices, each with a playable definition-of-done, an ordered step table with
    planned files, and the tuning knobs it exposes. M1 = smallest playable interaction
    (movement + first kill-equivalent). If the GDD carries a draft ladder, refine it
    rather than inventing a new one.
  - `CLAUDE.md` — read-first pointers to the trio, hard conventions and pre-seeded gotchas
    (both from `knowledge.md`), a current-status section, useful commands (headless
    smoke-test, gate).
- **Gate skeleton now, not later:** `tools/check.sh` with import + load + boot legs (they
  need no game; anatomy in `../evaluation/knowledge.md` Part C). Verify it runs green on
  the empty project.
- Commit (structured message), and from here: gate before every hand-back.

## Phase 2 — The milestone loop (repeat per milestone)

For the current milestone in `PLAN.md`:

1. **Orient.** Re-read the doc trio (sessions are stateless). State the milestone and its
   definition-of-done in one line before touching code.
2. **Implement step by step.** Headless smoke-test after each coherent change; gate
   (`--fast` once a balance leg exists) while iterating; commit per step.
3. **New mechanic ⇒ same-step gate extension** — a unit test for its logic; bot support
   once the harness exists (eval-debt rule #1 in `../evaluation/knowledge.md` §C3).
4. **Milestone end:** full gate green → update `PLAN.md` (mark done; refine the remaining
   ladder if the milestone taught you something) and `CLAUDE.md` (status, key-files map,
   any new gotcha) → **hand back**: what was built, the gate verdict, the 1–3 things only
   a human can judge (feel), TUNABLE choices you made, OPEN items you hit.
5. **Stop after the hand-back.** The human's feel feedback typically becomes a small
   data-only tuning step before the next milestone — that's the system working, not a
   failure.

**Escalate instead of pushing through:** design ambiguity the ledger doesn't cover · the
same gate failure after 3 distinct fix attempts · anything requiring a band change you
can't justify as a deliberate retune.

## Phase 3 — The evaluation leg (when the core loop is playable)

Earliest viable slot: right after the survival-loop milestone (player can play, die, and
win something — bot seams are cheap then). Run `../evaluation/prompt.md` end to end:
seams, policy ladder, observer, `--fixed-fps` fidelity check, difficulty target taken
from the GDD's difficulty-intent section, balance leg + bands wired into the gate.

From here the **full gate** is the hand-back criterion for every change.

## Phase 4 — Prototype completion

- All milestones ☑, gate green, difficulty in band per the GDD's stated intent.
- Final hand-back: the difficulty fingerprint table, honest caveats (unmodeled parts +
  error direction, bot validity), confirmation that backlog items stayed behind the
  fence — and, in a replication trial, stop there: the **human** grades against the
  control, not you.

## Definition of done

One repo containing: the doc trio (current, not stale) · a playable prototype matching
the GDD's scope contract · a green gate (`tools/check.sh`) with load/boot/unit/balance
legs · a difficulty fingerprint in the GDD's intended band · a git history of
milestone-shaped, structured commits.

## Anti-patterns (the short list — full list in `knowledge.md`)

- ❌ Building breadth-first instead of the vertical slice.
- ❌ Handing back "done" without the gate, or with "please check if it works".
- ❌ Deciding OPEN items silently; building DEFERRED items enthusiastically.
- ❌ Hardcoding numbers that belong in `.tres`/exported vars.
- ❌ Reading the control project during a replication trial.
