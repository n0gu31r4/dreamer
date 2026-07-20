# Kick-starting a Game From Zero — Knowledge Base

How an agent takes **(a buildable GDD + an empty directory)** to a scaffolded,
conventioned, gated Godot project and drives it to a complete prototype. Derived from
lab #1's actual history — ~24 commits from scaffold to prototype-complete to eval leg —
plus its three working docs. That build happened **once, with a human in the loop at every
milestone**, so everything here is ◐ PARTIAL until trial #1 re-executes it cold; items
marked ☐ INTENT are synthesized recommendations that diverge from what the lab literally
did.

Companion: `prompt.md` (same directory) — the operating procedure that applies this.

---

## The doc trio (the project's operating system)  ◐

Every lab runs on three documents with distinct jobs and change cadences:

- **`GAME_DESIGN.md`** — the *what*. Effectively frozen after step 0; edits are design
  changes (deliberate, human-approved).
- **`PLAN.md`** (lab #1 called it `PROTOTYPE_PLAN.md`) — the *how & in what order*. The
  milestone ladder; moves at milestone cadence.
- **`CLAUDE.md`** — the working guide: hard conventions, **current status**, a
  key-systems-by-file map, and accumulated gotchas. Moves every session. Lab evidence:
  this file grew into the project's memory — sessions are stateless, this file is not.
  A stale CLAUDE.md is the leading cause of a fresh session flailing.

Standing rule observed in the lab: **the docs are the spec** — if code and docs disagree,
the docs win and the disagreement is surfaced to the human.

## The milestone ladder (vertical slices)  ◐

- **Every milestone ends playable**, and the playable statement *is* the definition of
  done. Lab ladder: "you can move and kill" → "a real survival wave" → "the full roguelite
  loop" → "the complete 5-wave prototype".
- Milestone anatomy (from the lab's M1): definition of done + an ordered **step table with
  planned files** + the **tuning knobs** the milestone exposes.
- The ladder is approximately a **topological sort of the GDD's core loop**: smallest
  playable interaction first (movement + first kill-equivalent), then the fail state and
  the loop's spine (survival), then the meta loop (progression/economy), then content +
  polish.
- Ladders refine mid-build: the lab split M3→a,b and M4→a,b,c,d at natural playable
  boundaries. Expect it; record it in the plan doc, don't fight it.
- **One milestone at a time. Commit per step. Headless smoke-test before every
  hand-back.** The lab's git history is this discipline made visible — and it's what the
  milestone loop automates.

## When each verification leg can earliest exist

The lab installed the eval leg *after* the prototype was feature-complete (works, but the
playbook's own meta-principle — "the evaluation system is the product" — says earlier).
The synthesis:

- **Import + load + boot gate legs: at scaffold time.**  ◐ — these need no game at all and
  catch parse/reference/startup breakage from commit #1. (`../evaluation/knowledge.md`
  Part C for anatomy.)
- **Unit leg: when the pure-logic core exists** (stats/economy math — lab: M3).  ◐
- **Harness + balance leg: once the core loop is playable** (lab-earliest: after the
  survival-loop milestone — bot seams are cheap then). Feed `../evaluation/prompt.md` at
  that point.  ☐ INTENT — the lab did this much later; trial #1 tests the earlier slot.
- From the moment the gate exists, **gate-green is the hand-back criterion** — never
  "please playtest to check I didn't break something".

## The feel loop (where the human stays in the loop)  ◐

- The human playtests **at milestone boundaries** and gives mostly-numeric feedback. Lab
  evidence: the feel fixes were one-line data commits (`fire_rate 3.0 → 1.5`,
  `pickup_range 90 → 50`) — possible only because every number lived in `.tres`/exported
  vars. **Numbers in data is what makes taste cheap.**
- HITL points in a bootstrap, in full: GDD authoring (step 0) · feel checks at milestone
  ends · taste calls the GDD ledger marks OPEN · theme/art approval (later). Everything
  else runs on the gate.

## Conventions that paid off (adopt by default in new labs)  ◐

Typed GDScript · content as `.tres` resources (add a weapon/enemy = data, not code) ·
signals over polling · collision layers named by role · theme-agnostic systems code ·
all gameplay numbers in data/exported vars.

One more, ☐ INTENT (2026-07-19, from lab #2's device catch, not yet lab-proven): **input
read only through named input actions** (Godot: Input Map + runtime `InputMap` API), each
action bound for every supported device in the same commit that creates it — never raw
keycodes in scripts. Keys must always stay flexible: games eventually need configurable
bindings, and action indirection makes device switching and a future rebinding UI a
data/UI concern instead of a combat-code retrofit.

## Gotchas to pre-seed into a new lab's CLAUDE.md  ✅

All bitten and documented in lab #1; they are engine-general (Godot 4.x), not
game-specific — seed them so the new lab doesn't pay for them twice:

- A new `class_name` isn't visible to headless runs until the class cache regenerates —
  run `godot --headless --import` after adding one (cheapest cure: make `--import` the
  gate's first step).
- Never `add_child` a monitoring `Area2D` from inside a physics collision callback —
  defer it (`add_child.call_deferred`).
- A `PROCESS_MODE_ALWAYS` parent makes spawned children inherit ALWAYS and ignore pause —
  every gameplay entity sets `PROCESS_MODE_PAUSABLE` in `_ready()`.
- A stationary headless player barely levels (enemies trickle in) — force the XP curve
  temporarily to verify leveling; don't wait on natural play.
- The full landmine map (time-scale vs `--fixed-fps`, observer pattern, etc.):
  `../evaluation/knowledge.md` Part B.

## Experimental hygiene for replication trials  ☐ INTENT

When a trial replicates an existing game from its GDD: the building agent must **not read
the control project** — inputs are the GDD + dreamer's skills, nothing else. The control
exists for *grading afterwards*: milestones reached, where the build stalled or escalated,
doc quality, architecture/feel divergence, wall-clock and token cost. A peeked replication
proves nothing.

## Anti-patterns  ◐

- ❌ Breadth-first building (scaffolding every system at once) instead of the vertical
  slice — kills the feedback loop the whole method rests on.
- ❌ "While I'm here" scope creep mid-milestone — one milestone, playable, hand back.
- ❌ Hardcoded numbers — they break feel-tuning now and the harness later.
- ❌ Letting `CLAUDE.md`'s status/map sections go stale — they are the next session's eyes.
- ❌ Silently deciding an OPEN-ledger item because asking feels slow.
- ❌ Installing the gate "later" — load/boot legs cost minutes at scaffold time and pay
  from commit #1.
