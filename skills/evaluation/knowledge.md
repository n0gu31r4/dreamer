# Game Evaluation & Verification Systems — Knowledge Base

Generic, reusable knowledge for building the **evaluation leg of an automated game-development
loop**: systems that measure game quality (difficulty, and through it, *fun*), verify that
changes didn't break anything, and ultimately let an agent tune a game by **numbers instead of
feel**. Written from hands-on experience on a top-down arena survival roguelite in Godot, but
deliberately abstracted to apply to any game and (for the method parts) any engine.

Companion: `prompt.md` (same directory) — a ready-to-feed prompt that drives an agent to
build these systems on a new game, using this document as its reference.

**Confidence labels** (per the depth each section deserves):
- ✅ **PROVEN** — built, battle-tested, numbers verified. Trust the details.
- ◐ **PARTIAL** — built and working, but with known gaps stated inline.
- ☐ **INTENT** — designed but not yet built; high-level intention only. Expect to revise.

---

## Why this exists

The long-term goal is **automated game development**: an agent that writes code, art, *and
evaluates the result*. Evaluation is the hard leg — and it is really **two** legs:

1. **Measurement** — a machine-readable signal for "how hard / how good is this?" You cannot
   close an autonomous tuning loop without it. "Fun" feels unmeasurable; **difficulty is not**,
   and for most action/roguelite games difficulty is the dominant axis of fun. Quantify it
   rigorously, treat it as a tunable field, optimize toward a target band. The band *is* the
   fun model.
2. **Verification** — measurement frozen into **pass/fail assertions** (a regression gate).
   A metrics report is a dashboard; agents don't read dashboards, they need exit codes. The
   measurement system starts paying for itself the day its numbers become *asserted invariants*
   that turn red when a change breaks them. (Ours caught a real, week-old balance regression
   on its literal first run — see Part C.)

The measurement deliverable is a **difficulty fingerprint**: a small vector of numbers (per
wave / level / encounter) plus a single headline index, produced by simulating real gameplay
with bots — fast, deterministic, repeatable. The verification deliverable is **one command**
that answers "did I break the game?" in seconds, without a human playtest.

A meta-principle that shaped everything after the first session: **for automation, the
evaluation system is the product.** Invest in it *before* scaling content. Every system you
can measure is a system an agent can safely change.

---

# PART A — Engine-agnostic principles (the math & method)  ✅ PROVEN

These hold for any engine (Godot, Unity, Unreal, a custom loop) and even non-game simulations.

## A1. The one idea everything rests on: difficulty is *policy-relative*

> **Difficulty is not a property of the game. It is a property of the game *relative to a way
> of playing* (a policy).** A difficulty number measured without specifying the skill level
> that produced it is meaningless.

So you never ask "how hard is this game?" You ask "how hard is it *for this policy*?" and you
run a **ladder of policies of increasing competence**. The classic minimal ladder:

- **π₀ — idle / trivial probe.** Never moves, never acts optimally. Answers "can you win by
  doing nothing?" If yes, the game is broken-easy. *This is the single most informative probe
  you have — "stand still and survive" is a measurement, not a bug.*
- **π₁ — basic.** The simplest non-trivial survival heuristic (e.g. flee the nearest threat).
- **π₂ — skilled.** A competent proxy: avoid danger, exploit mechanics, use abilities.

The **gap between policies** is the real signal (see A2, "agency"). A game where π₀ already
wins is trivial; a game where even π₂ always dies is unfair; the sweet spot is where π₂
survives *on the margin* and the π₀→π₂ gap is large.

**A policy is more than movement.** A way of playing includes every recurring decision the
game offers: what to buy, what to level, when to spend consumables. If your game has a
meta-loop (shop/upgrades/economy), the policy ladder must ladder *those* decisions too —
see Part D for why leaving them out eventually poisons your numbers.

## A2. The three measurable axes of difficulty (with math)

Pick metrics that are **mechanistic** (derived from the sim's own quantities), not vibes.
For a combat/survival game these three axes cover most of it. Adapt the formulas to your genre.

**1. Lethality — can the threat actually drain the player?**
Let mitigated damage taken over an encounter be `D`, effective HP `eHP`, regen `r`, duration `T`.
```
Λ = D / (eHP + r·T)          # fraction of the player's HP budget the encounter consumes
```
- `Λ < 1` → a *passive* player survives (the danger is theoretical).
- `Λ ≥ 1` → the player is *forced* to mitigate; the fraction they must avoid is `(Λ−1)/Λ`.
- `Λ = 0` is a red flag: nothing is reaching the player — usually a *reachability* problem
  (player out-ranges/out-runs threats), not a damage problem. It is also the signature of
  silently broken collision detection (see B2) — treat a sudden Λ collapse as corruption
  until proven otherwise.

**2. Accumulation — does pressure build, or stay bounded?** Pure queueing theory.
Threats arrive at rate `λ` (spawns/sec) and are removed at rate `μ` (playerDPS / threat_eHP).
Load `ρ = λ/μ`:
- `ρ < 1` → threat count stays bounded → little contact → low lethality.
- `ρ ≥ 1` → count grows like `∫(λ−μ)dt` → swarm → runaway damage → death.

Measure it empirically via mean concurrent threats `N_mean`, peak `N_max`, and
**containment = removed/arrived** (≈1 means you keep up; <1 means you're being overwhelmed).
By Little's law, large `N_mean` relative to arrivals = threats live long = you're not clearing them.

**3. Skill demand (agency) — does playing well matter?** Compare outcomes across the policy ladder.
```
agency = outcome(π_skilled) − outcome(π_idle)     # e.g. HP% remaining, or survival probability
```
If π₀ already wins at full health, agency ≈ 0 → skill is irrelevant → boring for a skilled
player, regardless of how "busy" the screen looks. **High agency + π_skilled near the survival
threshold** is the target.

**Composite index (0–10).** A weighted blend of (lethality, accumulation, HP lost, fail rate),
measured under the *skilled* policy, gives a glanceable headline. But **always keep the vector**
`(Λ, N, agency, survive%)` — the scalar tells you *how hard*, the vector tells you *why*, and
you tune against the *why*.

## A3. Fun as a target band (flow)

Fun peaks where **challenge ≈ skill** (the flow channel). For a player who likes it hard, the
target band is shifted up. So "fun" is operationalized as: *difficulty, measured against the
intended player's skill, lands inside a target band.* Two implications:

- Define the band explicitly per difficulty tier (e.g. medium: π_idle dies, π_skilled wins
  ~70–80% on the margin, index peaks ~4–5).
- The ultimate calibration is **per-player**: record real play traces, fit a `π_human` policy
  to them, and measure difficulty against *that*. Then the band is personal and the difficulty
  number becomes a genuine *fun* proxy for that specific player. (☐ INTENT — see E4.)

**Known blind spot of difficulty-as-fun:** it cannot distinguish *hard and engaging* from
*hard and boring* (a bullet-sponge wave and a frantic dodge-fest can post the same Λ). The
planned guard is **pacing metrics** — kill-rate variance, threat-mix entropy, intensity-curve
shape over an encounter — so monotone pressure scores badly even when lethality hits its
target. (☐ INTENT — see E5.)

## A4. Monte-Carlo + determinism — and what determinism buys you

Single runs are noisy (RNG in spawns, crits, AI). Run **N trials per policy** and aggregate
(means, survival %, death-by-stage histograms). **Seed the RNG per (policy, trial)**
(`seed(base*i + policy.hash())`) so a re-run with the same code gives the same numbers.

Determinism is not just tidiness — it upgrades measurement into **attribution**:

- With fixed seeds, a metric change between two runs of the *same code* is impossible; so a
  change between two *commits* is **caused by the diff**. A band failure in the gate (Part C)
  is a real behavior change, never a flake. No flaky-test culture, no "rerun until green".
- It enables **historical bisection**: check out an old commit in a separate worktree
  (`git worktree add /tmp/old <sha>`), run the same harness with the same seeds, and compare.
  This is how we proved a 65%→0% win-rate collapse was introduced by one specific commit and
  not by measurement noise. Cheap, decisive, generic — use it whenever "did the game change
  or did the harness change?" comes up.

## A5. Tuning methodology — isolate, measure, iterate

The harness is only half the system; the other half is *how you use it*.

- **Isolate one lever per iteration** when diagnosing. Want to know what makes it easy? Change
  *only* the accumulation levers (spawn rate, threat HP) and watch which metric moves. Bundling
  changes hides causation. Once you understand the elasticities, you can move several at once.
- **Read the vector, not just the index.** `Λ=0` with high `N_mean` means "lots of enemies,
  none reaching you" → a reachability/speed problem, not a damage problem. The vector tells you
  which knob to turn.
- **Difficulty as a multiplier system.** Make difficulty a single continuous `level` (1.0 =
  your tuned base) feeding **per-dimension multipliers** applied at spawn time. Crucially,
  **each dimension scales on its own curve** because they have very different
  *difficulty-elasticity* (see A6). This gives you difficulty *selection* (easy/medium/hard)
  for free, and makes the base the thing you tune once.
- **Tune the base by measurement, not feel.** Set a target profile for the base tier, then
  iterate the base numbers until the harness reports it. Only *then* layer the multiplier tiers.

## A6. Hard-won general findings about difficulty levers

These emerged from real tuning and are likely **genre-general for top-down/action games**:

- **Relative speed is the dominant lever, and the least intuitive.** If the player moves faster
  than every threat, *optimal movement ≈ invincibility* — no amount of density or per-hit
  damage threatens a competent mover, because they just kite forever. The cure is **at least
  one threat as fast as or faster than the player** (kiting stops being free) and/or
  **inescapable area denial** (dense projectiles you must dodge, not outrun). Speed is *potent*:
  small changes cause large difficulty swings, so scale it gently.
- **Density and per-hit damage are gentle levers** against a skilled mover — they mostly punish
  *passive* play. Use them to set the floor (π₀ dies), not the ceiling.
- **Auto-fire that targets "nearest"** means the player can't focus a priority target (e.g. a
  boss) while adds are present — design encounters knowing the player's damage gets *diluted*.
- **Setpiece bosses should not inherit per-wave/per-level scalar ramps** meant for trash; a
  ramp stacked on an already-tanky boss makes an unkillable HP sponge. Scale setpieces explicitly.
- **The economy can be skill-gated by movement — measure it per policy.** If currency drops
  where enemies die and must be *walked over*, then a fleeing player collects almost nothing
  (it runs *away* from where drops land) while a confident weaving player funds a real build.
  Measured on our lab game: basic-flee banked ~0.5 currency/wave, skilled banked 9–18. This is
  a *desirable* emergent property (purchasing power itself sits on the skill ladder) — but only
  if you know it exists. Add **resource flow per policy per encounter** to the fingerprint;
  it explains build divergence that pure combat metrics can't.

## A7. Validity — the traps that make numbers lie

- **Your skilled bot must be a true skill ceiling.** If a *simpler* policy outperforms your
  "skilled" one in some regime (e.g. a naive flee-nearest beats a crowd-averaging repeller
  against a single fast pursuer), then your index *overstates* difficulty for a real expert.
  Verify `outcome(π_skilled) ≥ outcome(π_simpler)` everywhere; fix the bot if not.
- **The boundary of your model is the boundary of your guarantees.** Anything player power
  flows through that you don't simulate (shop, gear, meta-progression) is not a static
  caveat — it is a **time bomb**: the moment a design change moves weight into the unmodeled
  part, your baselines silently stop describing the real game (see Part D for the full story).
  Either model it, or pin it with an explicit tripwire assertion that fires when the design
  starts depending on it.
- **No silent truncation.** If a run caps something (top-N, timeouts, sampling), log it.
- **Fidelity check before trust.** Any speed/optimization hack must reproduce the slow,
  known-good baseline *exactly* before you trust its fast numbers (see B2 — this is where the
  biggest landmines live).

## A8. The measurement/control separation (architecture principle, engine-agnostic)

Keep **measurement** (sampling HP, counts, events every simulation step) separate from
**control** (deciding when a wave/encounter ends and advancing). Measurement must be tied to the
**simulation's own time step**, never to the harness's outer loop or to wall-clock — because the
moment you speed up the sim, any measurement that rides the outer loop will under-sample and
desync. The robust pattern: a per-step **observer** that the engine guarantees to tick once per
simulation step, which both records metrics and detects end-conditions; the outer control loop
merely *polls* it. (Concrete Godot implementation in B4.)

The same separation applies one level up: **the harness measures, the gate asserts** (Part C).
Keep assertion thresholds in a small standalone script that reads the harness's JSON output —
not inside the harness — so bands live in one obvious, editable, reviewable place.

---

# PART B — Godot-specific knowledge  ✅ PROVEN

Godot was chosen largely because it is the most **agent-automatable** engine: text scene/resource
formats (`.tscn`/`.tres`/`.gd`) and full headless CLI. But its main-loop and physics semantics
have sharp edges that *silently corrupt* an evaluation harness if you don't know them. This
section is the map of those edges.

## B1. Headless harness skeleton

- Run a **`SceneTree` script** as the entry point: `godot --headless -s res://tools/eval/harness.gd`.
  Override `_initialize()` and `call_deferred("_run")`; do the work in an `async` `_run()` using
  `await physics_frame` / `await process_frame`.
- **Build the world manually**: instance the player/enemy/spawner scenes, `add_child` them to a
  `Node2D` world you set as `current_scene`. Reset between trials by freeing the world.
- **Autoloads**: they exist under `root` at runtime (`root.get_node("Run")`,
  `root.get_node("Difficulty")`). If your top-level `preload`/`const` references an autoload
  *global by name*, it can fail to compile because the global isn't registered when the harness
  script first compiles. **Fix: `load()` game scripts at runtime inside `_run()`**, and fetch
  autoloads via `root.get_node(...)` rather than the global identifier.
- Write a human report to stdout **and** structured data to JSON (gitignore the JSON; it's output).

## B2. ⚠️ THE BIG ONE: how to speed up the simulation (and how NOT to)

You will want to run game-minutes of simulation in wall-seconds. There is a right way and a
seductive wrong way, and the wrong way fails *silently* (numbers look plausible, but are wrong).

**❌ Do NOT use `Engine.time_scale`.** It seems perfect ("a time multiplier, keep proportions,
run fast") but it works by running **multiple physics ticks per rendered frame** (batching).
That breaks collision detection for any `Area2D` that relies on overlap *monitoring* (see B3),
because area monitoring is flushed **once per frame, not per physics sub-step**. Result: fast-
moving projectiles/areas teleport past their targets between flushes, `body_entered`/
`area_entered` never fire, **nothing takes damage, lethality collapses to ~0**, and the whole
fingerprint is garbage — while the run still *completes and prints a confident report*. This is
the worst kind of bug. Raising `max_physics_steps_per_frame` does not save you; lowering it to 1
doesn't reliably help either once `time_scale` is in play.

**✅ DO use the `--fixed-fps N` CLI flag.** `godot --headless --fixed-fps 30 -s harness.gd`.
This advances game-time by **exactly `1/N` seconds per frame**, runs **one physics tick per
frame**, and runs frames **back-to-back at full CPU speed** with no real-time wall gate. Because
`dt` is fixed and there's exactly one tick per frame, **`Area2D` monitoring flushes every tick**
(collisions intact) and **the simulation is bit-identical to realtime** — only the wall clock
compresses. Measured impact: a full multi-wave × multi-policy run dropped from **~5 minutes to
under 1 second**, with numbers matching the realtime baseline exactly.

Mental model:

| | realtime (default) | `Engine.time_scale = K` | **`--fixed-fps N`** |
|---|---|---|---|
| Wall-clock pacing | gated to N ticks/real-sec | unpaced (fast) | **unpaced (fast)** |
| `dt` per physics tick | `1/N` | `1/N` | **`1/N`** |
| Physics ticks per frame | 1 | many (batched) | **exactly 1** |
| `Area2D` collisions | ✅ work | ❌ silently broken | ✅ work |
| Result fidelity | baseline | corrupted | **bit-identical** |

**Rule of thumb:** speed comes from removing the *wall-clock gate*, never from inflating `dt` or
batching ticks. `--fixed-fps` removes the gate while preserving one-tick-per-frame.

## B3. Why `Area2D` is the landmine: per-frame vs per-tick

Most lightweight game interactions (bullets, pickups, hit/hurt boxes, proximity contact) use
`Area2D` overlap **monitoring** (the `body_entered` / `area_entered` signals, or
`get_overlapping_bodies()`). That monitoring is resolved/flushed on a **per-frame** cadence, not
strictly per physics sub-step. As long as there's one tick per frame (realtime, or `--fixed-fps`)
this is invisible. The instant something makes >1 tick happen per frame (`time_scale`, heavy
batching), area detection samples a stale, leaping world and **misses overlaps**. Bodies with
the solver (`move_and_slide`/`move_and_collide`) are more robust, but anything reading *area
overlaps* will break. **If your combat depends on `Area2D` (it usually does), you are locked
into ≤1 tick/frame — which is exactly why `--fixed-fps` is the answer and `time_scale` is not.**

(If you ever *must* batch, the only real fix is to replace area-monitoring hit detection with
explicit per-tick distance/shape checks in `_physics_process` — an invasive gameplay change.
Prefer `--fixed-fps`.)

## B4. The observer-node pattern (don't measure from the `await` loop)

A natural-but-wrong harness measures inside its control loop:
```gdscript
while not done:
    await physics_frame
    t += dt              # ❌ assumes one resume == one physics tick
    sample_metrics()     # ❌ undersamples under fast pacing
```
The assumption "`await physics_frame` resumes once per physics tick" is **false** under fast
pacing: the coroutine resumes roughly **once per frame**, and frames decouple from ticks. The
loop then undercounts time, collapses HP curves to a couple of samples, and — worse — advances
waves at the wrong game-time, *truncating the actual simulation*.

**Fix: put all per-tick work in a node's `_physics_process`, which the engine guarantees to call
exactly once per physics tick**, regardless of frame/tick pacing. This "observer" node:
- accumulates time (`t += delta`, where `delta` is the fixed unscaled physics dt),
- samples metrics every tick (HP, concurrent threat count, seen-set for spawns/kills, HP curve),
- **detects end-conditions** (death, cleared, timeout) and snapshots the final outcome at the
  exact tick it ends (so outer-loop poll-lag can't skew results),
- exposes a `done` flag.

The harness control loop then just does `while not observer.done: await physics_frame` — its
resume cadence no longer matters. This makes the fast (`--fixed-fps`) sim *and* the realtime sim
produce identical measurements. (This is the Godot realization of principle A8.)

## B5. Fixed timestep is your fidelity anchor

Put **all gameplay logic in `_physics_process(delta)`**, which uses a **fixed** `delta`
(`1/physics_ticks_per_second`). `time_scale` does **not** change this `delta` (it changes tick
*count*); `--fixed-fps` sets it explicitly. Because every entity (player, bots, projectiles,
spawner, observer) advances by the same fixed `delta` per tick, the simulation is deterministic
and speed-invariant. Avoid putting sim-critical logic in `_process` (idle frame) — its `delta`
is wall-variable and frame-paced, so it desyncs under fast modes. Auto-fire, movement, spawn
timers, ability cooldowns: all `_physics_process`.

## B6. Pause / process-mode gotchas

If your gameplay scene is `PROCESS_MODE_ALWAYS` (e.g. so a HUD/restart works while paused),
children **inherit ALWAYS** and won't freeze on `get_tree().paused = true`. Every gameplay
entity that should freeze must set `process_mode = PROCESS_MODE_PAUSABLE` in `_ready()`
(player, enemy, projectile, pickup, spawner, camera, and the harness **observer**). Forgetting
one means it keeps simulating during a "frozen" between-wave state and corrupts measurements.

## B7. Determinism hazards

- **Seed per trial** (`seed(base*i + policy.hash())`) for reproducibility.
- **Wall-clock time / unseeded randomness** break reproducibility — drive randomness from the
  seeded RNG only; pass timestamps in from outside if needed. Note that *any* code consuming
  the seeded stream (e.g. a shop shuffling offers) is part of the deterministic replay — which
  is good, as long as nothing nondeterministic sneaks into the stream's consumers.
- New `class_name` scripts aren't visible to headless runs until the **global class cache** is
  regenerated: run `godot --headless --import` once after adding one (else "Could not find type
  X"). The cheapest cure: make `--import` the *first step of your gate* (Part C) so it can
  never be forgotten. Autoloads accessed by their node name avoid this.

## B8. Driving the player from a bot (the gameplay seams)

Add a minimal, duck-typed seam to the player: a `var bot = null` that, when set, **replaces input
reading** in `_physics_process` (`bot.move_dir(self)`, `bot.use_active(self, slot)`); otherwise
read real input as normal. Add a `damage_taken` accumulator for instrumentation. Keep bot
policies in their own file with **no `class_name`** (so iterating on them doesn't force a class-
cache reimport); the harness `preload`s that file and uses inner classes. Let bots perceive the
world through **groups** (`get_nodes_in_group("enemies")`, `"enemy_projectiles"`,
`"materials"`) — add entities to those groups in `_ready`/spawn so the bot can "see" them.
This is theme-agnostic and ships inert (bot is null in the real game).

If the game's real flow swaps scenes between encounters (arena → shop → arena) but the harness
keeps one persistent world, you need one more seam: a public **re-bind method** on the player
(e.g. `bind_loadout()`) that re-reads the loadout from the persistent run state — extracted
from `_ready` so spawn and harness use the same code path. (The real game "re-binds" by
re-instantiating the player; the harness calls the method.) See Part D.

## B9. Difficulty as data (Godot shape)

A `Difficulty` autoload holding a continuous `level` (1.0 = base) + per-dimension multiplier
methods (`hp_mult`, `damage_mult`, `speed_mult`, `spawn_mult`), applied by the spawner at spawn
time (and to spawn cadence). `level == 1.0` leaves all multipliers at 1.0, so your `.tscn`/`.tres`
base values *are* the tuned medium base. Presets are a dict (`easy/medium/hard/brutal → level`).
The harness sets `Difficulty.level` from a CLI arg to sweep tiers in one batch. Keep all of this
**theme-agnostic** and **data-driven** (numbers in `.tres`/exported vars, not hardcoded), so
tuning never needs a code change.

---

# PART C — From measurement to verification: the regression gate  ✅ PROVEN

A measurement harness becomes infrastructure the day it gains **pass/fail semantics**. The gate
is one command — `tools/check.sh` — that answers *"did I break the game?"* with an exit code,
in seconds, with no human playtest. Every agent change ends with "gate is green" instead of
"please playtest". This is the prerequisite for every other automation (an automated build loop
without a gate has no brakes).

## C1. Anatomy: four checks, layered cheap-to-expensive

| # | Check | Mechanism | Catches |
|---|-------|-----------|---------|
| 0 | **Import** | `godot --headless --import` | stale class cache (B7) — run it first, always |
| 1 | **Load** | walk `res://`, `load()` every `.gd`/`.tscn`/`.tres`; fail on null or non-compiling script. Mechanism note (lab #2, teeth-verified): a broken GDScript still `load()`s as a **non-null** object — Godot only logs the parse error — so a null-check alone has no teeth; call `can_instantiate()` on every loaded `GDScript` to actually catch it | parse errors, broken scene/resource references, bad data edits — including *cascades* (one broken `.tres` fails every script that preloads it) |
| 2 | **Boot** | `godot --headless --quit-after 1` | autoload/startup crashes |
| 3 | **Unit** | a headless `SceneTree` script exercising the game's pure-logic core via its real APIs | logic regressions in economy/loadout/leveling math |
| 4 | **Balance** | full harness batch (N seeded runs/policy) + a small assert script over its JSON | tuning drift, broken collisions (Λ→0), difficulty regressions |

Provide a `--fast` flag that skips the expensive leg (ours: full gate ~20s, fast ~3s) so the
gate is cheap enough to run *while iterating*, not just before commit. Each step runs captured;
on failure print the captured output. Plain shell + a tiny Python assert script is plenty.

Two checks deserve special mention:

- **The unit leg targets the meta-loop math** (buy/sell/refund/stack/equip/level/buff-expiry).
  This is where agent-written changes silently break invariants, it's pure logic (no physics,
  millisecond-fast), and it's testable through the same public APIs the real UI calls. ~40
  focused checks cover a whole shop/inventory system. Test *invariants and intent*
  ("selling never orphans a stat modifier", "you can never sell your last weapon"), not
  implementation details.
- **The balance leg gets physics-sanity tripwires** alongside the difficulty bands: assert
  `kills > 0` (player projectiles connect) and `idle damage_taken > 0` (enemy contact
  connects). These directly catch the silent Area2D-collision failure mode (B2/B3) — the
  single scariest corruption — the moment it appears, regardless of what causes it next time.

## C2. Band policy — the social contract that keeps the gate honest

Bands (e.g. "skilled wins 50–95% at medium", "idle never wins", "basic-flee ≤ 25%") live at
the top of the assert script, in one obvious place. The policy, stated in the file itself:

> **Bands change ONLY in a commit that deliberately retunes the game, with the new measured
> baseline in the commit message. An unexpected band failure is a regression — never widen a
> band to silence it.**

Because the harness is seed-deterministic (A4), a band failure is *always* a real behavior
change. This kills the two failure modes that rot CI cultures: flaky tests ("rerun it") and
threshold creep ("just bump the limit").

Width matters: bands must absorb *intended* small tuning drift while catching collapses. We
band the headline outcomes (win rates per policy, early-encounter survival/HP) rather than
every metric — over-asserting turns every tweak into band churn.

## C3. The maintenance model — what auto-updates and what must not

The gate has two kinds of parts, and the distinction is the whole design:

- **Discovering parts update themselves.** The load leg walks the filesystem; the harness runs
  the *real game code* (real player scene, real weapons, real spawner — no parallel model to
  drift). New content and changed numbers are covered with zero edits.
- **Asserting/deciding parts must stay manual** — unit tests, bands, bot decision rules.
  Their going stale *is the signal*. A test that auto-updated to whatever the code now does
  would assert nothing; a band that auto-widened would rubber-stamp regressions.

The resulting per-change maintenance cost, which is the table to design toward:

| Change | Gate maintenance |
|---|---|
| New content (a new item/enemy/character data file) | **None** — discovery + data-driven valuation (D2) absorb it |
| Tuning numbers (damage, hp, costs, curves) | None in code; re-baseline bands if balance shifts (deliberate commit) |
| Changed mechanic (e.g. weapon leveling works differently) | Edit the one matching unit-test function; maybe re-baseline |
| New *kind* of decision (new active type, new shop action) | Above + teach the bot policy the new choice |

The last row is **eval-debt rule #1**: any combat- or build-relevant mechanic ships with bot
support, or the difficulty index silently stops measuring real play. Make it a review
checklist item — it is not automatically detectable.

## C4. War story (why all of this is worth it)

On its **first ever run**, our gate's balance leg failed: skilled win rate 0%, banded 50–95%.
Not a flake (deterministic seeds), not a band problem. A worktree bisect (A4) showed the same
seeds winning 65% one commit earlier. Cause: a (good!) design change a week prior had moved
the player's second starting weapon into the shop — and the harness didn't model the shop, so
harness-skilled fought the whole game with half the firepower the tuning baseline assumed.
The game had silently become unmeasured; nobody noticed for a week because nothing asserted.

Lessons, all generic: (1) a measurement system without assertions detects nothing; (2) the
unmodeled boundary is where it breaks (→ Part D); (3) deterministic seeds + worktree bisect
turn "weird number" into "this commit did it" in minutes. Bonus: the gate's *other* legs
caught two injected/incidental failures the same day (a parse error in a freshly written test
file, a broken resource reference cascade) — layered cheap checks catch your tooling's own
mistakes too.

---

# PART D — Model the full player loop (meta-systems)  ✅ PROVEN

## D1. The principle: unmodeled subsystems are time bombs, not caveats

If player power flows through a meta-loop (shop, upgrades, crafting, gear), a harness that
only simulates combat measures a *hypothetical* game. The error isn't constant — it's a
**function of design decisions you haven't made yet**. The day the design shifts weight into
the meta-loop (our case: "start with one weapon, buy the second"), every baseline silently
inverts from "slight over-estimate" to "wildly wrong". Two valid responses:

- **Model it** (this part), or
- **Tripwire it**: assert the assumption that makes not-modeling safe (e.g. "the starting
  loadout is the full loadout"), so the gate fires the day the assumption dies.

Modeling won here, and was ~150 lines. It also upgraded the measurement: the fingerprint now
describes *the game players actually play* (build progression included), and it surfaced an
emergent economy finding (A6) that combat-only simulation could never see.

## D2. The greedy meta-policy pattern (with data-driven valuation)

Between encounters, run a **greedy policy over the real meta APIs** — the same
`can_acquire`/`acquire`/`spend` calls the real UI dispatches. Never reimplement shop rules in
the harness; call the game's own.

The hard part is valuation: "is this offer worth its cost?" across heterogeneous offers
(weapons, gear, stat items, consumables) **without hardcoding knowledge of any specific
item** (which would violate the C3 table's first row). The trick that makes it fully
data-driven:

1. **Probe, don't parse.** To value a stat-modifier bundle, temporarily apply it to the *live*
   stat block, read the resulting delta, and remove it (`add_modifier("__probe", …)` →
   `get_value()` → `remove_source("__probe")`). This prices percent-stacking, diminishing
   returns, and trade-off items (negative entries) correctly *for the current build state* —
   for free, because the game's own aggregation math computes it.
2. **Normalize in the game's own currency of improvement.** Divide each probed delta by the
   delta that one standard level-up boost of that stat would produce right now (probed the
   same way). Now every offer is priced in "boost-equivalents" — a unit that stays meaningful
   as the game's numbers evolve, with zero constants to maintain.
3. **Weight by a survival-utility table** (the same per-stat weights the between-encounter
   level-up policy uses — share one table).
4. A few **structural rules** for things mods can't express: filling an empty weapon slot is
   worth a large constant (a whole second gun); leveling an owned weapon is worth its
   data-declared per-level gain scaled by that weapon's share of total output; one-encounter
   consumables get a discount and are banked for the boss/setpiece.
5. **Greedy loop with re-valuation**: buy the best value-per-cost offer above a junk
   threshold, then *re-value everything* (the purchase changed the stat state), repeat;
   bounded reroll hunting if the shop allows rerolls.

Result: new content added to the pools is valued automatically — the policy bought sensible
builds (second gun first, then armor, banking buff potions for the boss) with no per-item
knowledge anywhere in the harness.

**Probe side-effect gotcha:** probing a live stat block fires its change signals; listeners
(e.g. "heal on max-HP gain") may react. Sequence probes where side effects are immediately
overwritten (we shop right before a full-HP wave start), or verify your probes are
side-effect-free in your game.

## D3. Mirror the real between-encounter sequence exactly

Whatever the real game does between encounters, the harness must do — in the same order. Ours:
expire one-encounter buffs → resolve banked level-ups → shop → discard uncollected floor
currency (the real scene swap destroys it — easy to miss and it inflates bot economies) →
restore HP per the game's rule → re-bind the player's loadout (B8 seam). Each divergence from
the real sequence is a small systematic bias; they compound.

## D4. Honest residual gaps (state them next to results)

Even modeled, bots are a *floor* on real-player economy, not a ceiling: ours don't *seek*
currency drops, only collect them en route (a real player routes through them). The skilled
bot's movement ceiling (A7) still binds. Difficulty read from bot play is now a *slight*
over-estimate, with the error direction known and stated.

---

# PART E — The wider automation harness (roadmap-level)

Systems beyond measure+verify, in increasing distance from what's built. Each lives or dies by
the gate: **every loop below uses "gate green" as its brake**. Keep a per-project
`AUTOMATION_PLAN.md` with phase statuses so any session can pick up where the last left off.

## E1. The automated milestone loop  ☐ INTENT (designed; experiment protocol defined)

The build loop itself becomes a command (`/milestone`-style): read the design/plan docs for the
next single step → implement following project conventions → run the gate, iterate until
green (extending the gate per the C3 table when the step adds mechanics) → commit with a
structured message → hand back a summary + what to evaluate for *feel*. The human reviews
diffs and taste, not process. **Run it as an experiment first**: 2–3 small backlog items,
grading each (did it scope correctly? did the gate catch its mistakes? was review trivial?)
and tightening the loop prompt between runs. Prerequisite: Part C, or the loop has no brakes.

## E2. Visual evaluation  ☐ INTENT

The eval legs so far are blind — they verify logic and balance, never pixels. Catches nothing
about invisible sprites, broken layouts, z-order, overlapping UI. Two planned probes:
- **Screenshot harness**: boot each scene headless-rendered (xvfb / `--write-movie` /
  RenderingServer capture), advance N frames, dump PNGs; an agent with vision reviews them
  against a short per-scene checklist. The prototype for the "art evaluation" leg, the way
  the difficulty harness was for tuning.
- **UI-bot flow test**: inject the engine's UI actions (`ui_*`) to walk the real menu graph
  (menu → character select → game → shop → game), asserting each transition fires. Makes the
  front-end — which the combat harness deliberately skips — regression-testable.

## E3. Closed-loop balance tuning  ☐ INTENT (the harness already takes a difficulty arg)

Today: harness measures, agent iterates numbers by hand. Next: "tune X to target Y" as one
command — the harness accepts **parameter overrides** (JSON/CLI, never editing data files
mid-search), a search script (coordinate descent / bisection over the known levers — start
with speed, A6) optimizes toward an objective band ("skilled wins 70±5%"), and outputs a
proposed data-file diff + before/after fingerprint for review. At ~1s per Monte-Carlo batch
this is cheap. Ties into content generation: "add an enemy" = generate data → gate → measure
difficulty delta → auto-tune its numbers into a target band.

## E4. Human traces & per-player calibration (π_human)  ☐ INTENT

The flow-channel endgame (A3): record real play traces (inputs + per-tick state), fit a
`π_human` policy, add it to the ladder, and set difficulty targets relative to *the actual
player's* measured skill — turning the difficulty index into a personal fun proxy. **Build the
trace recorder early** — it's small while the game is small, painful to retrofit, and the
traces double as golden regression data for the gate.

## E5. Pacing metrics (the "hard but boring" guard)  ☐ INTENT

Difficulty-in-band is necessary, not sufficient (A3 blind spot). Candidate mechanistic pacing
signals, all computable from the observer's existing per-tick stream: kill-rate variance over
an encounter (monotone grind vs. peaks-and-valleys), threat-mix entropy over time (variety),
intensity-curve shape (does pressure *build*, or sit flat). Target: monotone waves score
badly even at on-target lethality. Unvalidated — treat as hypotheses to measure against
human judgment first.

---

## TL;DR checklist (Godot eval+verify system)

1. `SceneTree` script entry; load game scripts at runtime; autoloads via `root.get_node`.
2. **Run it with `--fixed-fps 30`.** Never `Engine.time_scale` (breaks `Area2D` collisions).
3. **Observer node** does per-tick sampling + end-detection; control loop only polls `done`.
4. All sim logic in `_physics_process` (fixed `dt`); `PROCESS_MODE_PAUSABLE` on every entity.
5. Bot seam on the player (`var bot`); policies in a no-`class_name` file; perceive via groups;
   public loadout re-bind method if the real game swaps scenes between encounters.
6. Policy ladder idle/basic/skilled; Monte-Carlo with per-trial seeds; seeds make failures
   attributable (worktree bisect to pin the commit).
7. Metrics: lethality Λ, accumulation ρ/`N_mean`/containment, agency, resource flow per
   policy, composite index — keep the vector.
8. **Validate fidelity**: fast run must match the realtime baseline exactly before you trust it.
9. **Model the meta-loop** (shop/upgrades) via the game's real APIs with probe-based,
   boost-equivalent valuation — or tripwire the assumption that lets you skip it.
10. **Freeze it into a gate**: import → load-everything → boot → unit (meta-loop math) →
    balance bands + physics-sanity tripwires. `--fast` mode. Band policy: bands move only in
    deliberate retune commits. Run it after every change.
11. Difficulty = autoload `level` → per-dimension multipliers (speed scales gently); base = the
    thing you tune by measurement; tiers come free.
12. Report honestly: state what's unmodeled and the error direction; verify the skilled bot is
    a real skill ceiling; keep `AUTOMATION_PLAN.md` phase statuses current.
