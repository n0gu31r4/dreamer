# Prompt: Build the Evaluation & Verification System for this Game

> Feed this file to the agent on **any game you are autonomously developing** to have it build
> the evaluation leg: the measurement harness (difficulty → fun signal) AND the regression gate
> (pass/fail verification). It assumes Godot but the method is engine-general.
>
> **Reference:** `knowledge.md` (same directory) is the detailed knowledge
> base. Read it first; this prompt is the operating procedure that applies it. When in doubt on
> *why*, consult that file — especially Part B (Godot landmines), Part C (the gate), and
> Part D (meta-loop modelling).

---

## Your role and goal

You are building the **evaluation leg** of an autonomous game-development loop. Two deliverables:

1. A **headless, fast, deterministic harness** that simulates real play with bots — including
   the game's meta-loop (shop/upgrades), not just combat — and emits a **difficulty
   fingerprint**: a small metrics vector plus a 0–10 index per encounter/wave/level. This is
   the signal that lets us *autonomously tune the game toward fun*. Fun is operationalized as:
   **difficulty, measured against the intended player's skill, lands in a target band** (the
   flow channel; shifted up for players who like it hard).
2. A **regression gate** — one command, exit-code semantics — that freezes the fingerprint
   (and the rest of the project's health) into asserted invariants. Every change you make from
   then on ends with "gate green", not "please playtest". The gate is the brake that every
   later automation (build loops, auto-tuning) depends on.

Treat difficulty as **fully measurable and policy-relative**. Reason quantitatively; propose
*measurable* targets and verify them with the harness rather than asking for playtests-by-feel.

## Operating principles (non-negotiable)

1. **Measure relative to a policy ladder**, never in the abstract. The "stand still and survive"
   probe is your most informative test, not a joke. A policy includes *meta decisions* (what to
   buy/level), not just movement.
2. **Speed the sim with `--fixed-fps`, never `Engine.time_scale`** (the latter silently breaks
   `Area2D` collisions → corrupt numbers). See knowledge §B2/B3.
3. **Per-tick measurement lives in an observer node**, not the harness's `await` loop. See §B4.
4. **Validate fidelity**: any speedup must reproduce the realtime baseline *exactly* before you
   trust it.
5. **The boundary of the model is the boundary of the guarantees** (§A7/§D1). Model every
   system player power flows through, or tripwire the assumption that lets you skip it.
6. **Measurement without assertion detects nothing** (§C). The harness isn't done until its
   numbers are banded in a gate with a band-change policy.
7. **Keep it theme-agnostic and data-driven.** Numbers live in resources/exported vars; the
   harness and bots never name the game's theme; valuation is probe-based (§D2), never
   per-item knowledge.
8. **Report honestly**: keep the metrics *vector* (not just the index), state what you didn't
   model and the error *direction*, and confirm your skilled bot is a true skill ceiling.

## Procedure

### Phase 0 — Understand the game (read, don't assume)
- Read the design docs and the code. Identify: the core loop, what damages the player, what the
  player does to win, the time/encounter structure (waves/levels/rooms), enemy/threat types,
  the player's effective HP / mitigation / regen, movement speed, how *offense* works
  (auto-fire? aimed? abilities/cooldowns?), and **the full power loop** — every channel through
  which player power grows (XP/levels, shop, gear, items, meta-progression).
- Find the **tunable surface**: which numbers live in data (`.tres`/exported) vs hardcoded.
  Note anything hardcoded that should be data (flag it; move it if cheap).
- Identify the collision/detection mechanism (is combat `Area2D`-monitoring based? — it usually
  is, which locks you to ≤1 tick/frame; plan for `--fixed-fps`).

### Phase 1 — Add the minimal gameplay seams (smallest possible footprint)
- **Player bot seam**: `var bot = null` that, when set, replaces input in `_physics_process`
  (`bot.move_dir(self)`, `bot.use_active(self, slot)`); plus a `damage_taken` accumulator. Ships
  inert (null in the real game). See §B8.
- **Perception via groups**: ensure threats, threat-projectiles, and collectible resources are
  added to groups the bot can query (`"enemies"`, `"enemy_projectiles"`, `"materials"`, …).
- **Loadout re-bind seam** if the real game swaps scenes between encounters: a public method on
  the player that re-reads the loadout from persistent run state (extracted from `_ready`).
- That should be the *entire* gameplay-code change. Everything else lives in the harness/tools.

### Phase 2 — Define policies (the skill ladder)
Put them in one file with **no `class_name`** (avoids class-cache reimports); duck-typed for the
bot seam. Minimum ladder:
- **idle** — never moves/acts. Triviality probe.
- **basic** — flee the nearest threat; stay off walls.
- **skilled** — avoid crowds, dodge incoming projectiles, use abilities on clusters; a competent
  proxy. **It must be a valid skill ceiling** — verify it never does worse than a simpler policy;
  if it does (e.g. crowd-averaging steers it into a single fast pursuer), fix it.

### Phase 3 — Build the harness
- `SceneTree` entry script (`-s`), run with `--fixed-fps 30` (or your tick rate). Load game
  scripts at runtime; get autoloads via `root.get_node`. See §B1.
- **Observer node** (§B4): per-tick sampling of HP, concurrent threat count, spawn/kill set, HP
  curve; per-tick end-detection (death / cleared / timeout) with outcome snapshotted at the end
  tick; exposes `done`. The control loop only polls `done`.
- All entities (including the observer) set `PROCESS_MODE_PAUSABLE` if your scene is ALWAYS (§B6).
- Monte-Carlo: N trials per policy, **seeded per (policy, trial)** — determinism is what makes
  later gate failures attributable (§A4).
- Output: human report to stdout + JSON data file (gitignore the JSON).

### Phase 4 — Model the meta-loop (between encounters)  [knowledge §D]
- Mirror the real between-encounter sequence **exactly and in order** (buff expiry, level-up
  resolution, shop, resource cleanup matching the real scene swap, HP rules, loadout re-bind).
- Drive purchases through the game's **real APIs** (never reimplement shop rules) with a greedy
  policy whose valuation is **probe-based and normalized in boost-equivalents** (§D2) — so new
  content is valued automatically and the harness needs zero edits for content additions.
- Add **resource flow per policy per encounter** to the fingerprint (economies can be
  skill-gated — §A6 — and you want to see it).

### Phase 5 — Metrics (compute these; keep the whole vector)
Per encounter, under each policy (adapt formulas to genre — see knowledge §A2):
- **Lethality** `Λ = damage_taken / (eHP + regen·T)`. `Λ=0` ⇒ reachability problem — or broken
  collisions; check before believing.
- **Accumulation**: `N_mean`, `N_max`, `containment = removed/arrived`, load `ρ = λ/μ`.
- **Agency** `= outcome(skilled) − outcome(idle)` (HP% or survival%).
- **Composite index 0–10**: weighted blend of (lethality, accumulation, HP lost, fail rate)
  under the skilled policy. Report it *with* the vector and per-encounter HP-curve sparklines.
- **Run outcomes**: win%, reached-final%, death-by-encounter histogram, shop purchases,
  resources collected — per policy.

### Phase 6 — Validate fidelity (gate before trusting anything)
- Run the harness at realtime (no `--fixed-fps`) on a couple of encounters; record numbers.
- Run with `--fixed-fps`; confirm **identical** numbers and a large wall-clock speedup.
- If they differ, you have a pacing/sampling desync (re-check §B2–B4) — fix before proceeding.

### Phase 7 — Establish the base difficulty by measurement
- Add a `Difficulty` autoload: continuous `level` (1.0 = base) → per-dimension multipliers
  (`hp/damage/speed/spawn`), applied at spawn time + cadence. **Speed scales gently** (potent
  lever), hp/spawn near-linear. `level=1.0` ⇒ base = the data values. Presets dict for tiers.
- Set an explicit **target profile** for the base tier (default "medium"):
  - π_idle **dies** (no standing-still win) — your hard floor.
  - π_basic reaches the end but generally loses.
  - π_skilled **wins ~70–80% on the margin**, losing real HP through the run.
  - index ramps smoothly across encounters; `Λ < 1` (passive eventually dies, active survives).
- **Iterate the base data numbers** (one lever at a time while diagnosing) until the harness
  reports the target. Use the knowledge in §A6 — if a skilled mover is untouchable, the lever is
  almost always **relative speed** (give a threat ≥ player speed), not density/damage.
- Then sweep presets (easy/medium/hard/brutal) and confirm a sensible monotonic ladder.

### Phase 8 — Freeze it into the regression gate  [knowledge §C]
- One script (`tools/check.sh`), layered cheap→expensive, non-zero exit on any failure:
  **import refresh** (class cache) → **load** (walk the project, load every script/scene/
  resource) → **boot** (main scene, one frame) → **unit** (the meta-loop math through its real
  APIs — buy/sell/refund/stack/level/buff-expiry invariants, ~dozens of focused checks) →
  **balance** (a seeded harness batch + a small assert script over its JSON).
- Balance assertions = the Phase-7 target profile as **bands** (win-rate ranges per policy,
  early-encounter floors) **plus physics-sanity tripwires** (`kills > 0`, `idle damage > 0`)
  that catch silent collision breakage forever after.
- Write the **band policy into the assert file**: bands move only in deliberate retune commits,
  with the new measured baseline in the commit message; never widen a band to silence a failure.
- Add a `--fast` flag (skip the balance leg) for inner-loop use. Target: full gate well under a
  minute; fast mode a few seconds.
- **Prove the gate catches failures** before trusting it: inject a parse error, a broken
  resource reference, and a balance-relevant change; confirm red each time; restore.
- From this point on: run the gate after every change; "gate green" replaces "please playtest"
  as your hand-back criterion. Maintenance model: knowledge §C3 (content=free, numbers=maybe
  re-baseline, mechanics=edit the matching test, new decision kinds=teach the bots).

### Phase 9 — Report and document
- Present: the fingerprint table (per tier / per encounter), the headline indices, the key
  causal findings (which lever does what), and **explicit caveats** (residual unmodeled parts
  with error direction, bot-validity status).
- Update the project's working-guide doc with: how to run the harness and the gate, the tuned
  base profile, the band policy, and the difficulty-lever findings. Create/maintain an
  `AUTOMATION_PLAN.md` with phase statuses (gate → build loop → visual eval → auto-tune →
  π_human; knowledge §E) so any future session knows where the automation stands.
- Commit in coherent steps (seams+harness; speedup+observer; meta-loop policy; difficulty
  system+base; gate). Gitignore generated reports.

## Definition of done
- One command produces a deterministic difficulty fingerprint for any difficulty tier in
  **seconds**, matching realtime exactly — with the meta-loop (shop/upgrades) modelled through
  the game's real APIs.
- The base tier hits its measured target (idle can't win; skilled wins on the margin).
- Difficulty is a single tunable `level` with a sane easy→brutal ladder.
- **The regression gate exists, is green, provably catches injected failures, and carries the
  band policy.** New content requires zero harness/gate edits (verified by the data-driven
  valuation design).
- Caveats and the skilled-bot validity are stated. The autonomous loop now has its signal AND
  its brakes.

## Anti-patterns (do not do these)
- ❌ Speeding up with `Engine.time_scale` / batching ticks per frame.
- ❌ Measuring time/metrics by counting `await physics_frame` resumes.
- ❌ Trusting fast-run numbers without a realtime fidelity check.
- ❌ Reporting only the scalar index (hides *why*).
- ❌ A "skilled" bot that a simpler bot beats (inflates difficulty).
- ❌ Tuning by feel, or hardcoding balance numbers that should be data.
- ❌ Applying trash per-encounter scalar ramps to setpiece bosses (unkillable sponge).
- ❌ Leaving a power-relevant subsystem (shop/gear) unmodeled *and* untripwired — design drift
  will silently invalidate every baseline (knowledge §C4 war story).
- ❌ A metrics report with no assertions — dashboards detect nothing; agents need exit codes.
- ❌ Widening a band, auto-updating a test, or rerunning until green. Staleness of the
  asserting parts is the signal (knowledge §C3).
- ❌ Reimplementing game rules (shop logic, stat math) inside the harness — call the real APIs,
  or the model drifts from the game.
- ❌ Hardcoding per-item knowledge in bot valuation — probe mods against the live stat block
  and normalize in boost-equivalents instead (knowledge §D2).
