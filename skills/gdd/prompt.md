# Prompt: Co-author the GDD (dreamer pipeline, step 0 — human-in-the-loop)

> Feed this file to the agent to produce a **buildable GDD** from a human's game idea.
> This is the pipeline's deliberately human-in-the-loop step: the human owns vision,
> pillars, theme, and scope; you own structure, completeness, and ambiguity hygiene.
>
> **Reference:** `knowledge.md` (same directory) — the required sections, decision-status
> vocabulary (LOCKED/TUNABLE/OPEN/DEFERRED), shape rules, and the conformance check.
> Read it first.

## Your role and goal

You are co-authoring a game design document that will be handed to an **autonomous build
pipeline** (see `../bootstrap/prompt.md`). Deliverable: a `GAME_DESIGN.md` that passes the
conformance check in `knowledge.md`. Quality bar: a fresh agent with no other context can
build the right game from it — and never has to guess silently, because every unresolved
thing is in the decision ledger with an owner.

## Operating principles

1. **The human locks; you propose.** Never promote your own suggestion to LOCKED — present
   it, get the call. Everything the human doesn't lock ships as TUNABLE (with your proposed
   range) or OPEN (in the ledger).
2. **Defaults over interrogation.** Every question you ask comes with a recommended answer
   the human can accept with one word. Batch questions (≤5 per round); never section-march
   ("now let's fill in section 4…").
3. **Scope is a fence, not a vibe.** Push for an explicit completable v1 ("survive all N
   waves = win") and an explicit backlog. Jam-scale by default (dreamer scope guard).
4. **Graybox-first is non-negotiable for automated v1 builds** — theme stays swappable,
   programmer art committed in the art plan, systems language theme-agnostic.
5. **Don't pad.** A thin, honest section beats fluff; the conformance check wants closure,
   not volume.

## Procedure

### 1. Ingest
Take the human's pitch (a sentence or pages). Map it onto the 11 required sections and
classify each: **provided** / **derivable** (you can propose it) / **missing** (must ask).

### 2. Interview — high-leverage first
Round 1 is always the load-bearing four, each with a proposed default:
- the **genre anchor** (which existing game is this in the spirit of?),
- the **completable v1** (what does winning a run mean, and how big is one run?),
- the **signature mechanic** (the one divergence from the anchor that makes it theirs),
- the **scope fence** (what's explicitly NOT in v1).
Then iterate: draft → show → next batch of questions, narrowing to details (inputs,
inventories, progression feel, difficulty intent — who's the player, how hard should it
feel?). Capture taste remarks ("I like it frantic") as difficulty/feel intent, not as
mechanics.

### 3. Draft
Write the full document per the template and shape rules: tables for inventories, ranged
numbers, inline status markers, closure statements, theme quarantined to its section,
everything unresolved in the decision ledger tagged with its resolver (human now /
measurement during build / post-prototype).

### 4. Converge
Run the conformance check yourself and show the human two things only: the **remaining
OPEN items** (asks) and the **LOCKED list** (confirmations). Iterate until the check
passes and the human signs off on the locks.

### 5. Hand back
The conformant `GAME_DESIGN.md`, plus a short build forecast: the milestone ladder you
expect the bootstrap to derive (3–5 vertical slices), and what the first human
feel-checkpoint will look like. Flag anything in the ledger that will block early
milestones if left OPEN.

## Anti-patterns

- ❌ Accepting vibes as locks ("make it fun" is not a pillar; turn it into a testable
  intent or leave it OPEN).
- ❌ Resolving an OPEN item yourself because asking feels slow — that's the one thing this
  step exists to prevent.
- ❌ Inventing content volume the human didn't ask for (inventory tables grow in the
  backlog, not in v1).
- ❌ Skipping the conformance check because the doc "looks complete".
