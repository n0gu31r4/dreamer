# CLAUDE.md — working in the dreamer repo

Dreamer is the orchestrator + harness for automated game development (GDD → finished game). Read `README.md` for vision/architecture/stack, `PLAN.md` for current statuses and the next step. Labs are sibling repos (lab #1: `../new-game/`) with their own plans and conventions — when working in a lab, its `CLAUDE.md` and eval-debt rules govern.

## How we develop (the working agreement)

Work happens at three altitudes; the human picks the altitude per turn:

1. **Discuss** — design conversations. The output is decisions, and decisions land in docs (`README.md`, `PLAN.md`, skill files) — **the docs are the spec**. No implementation until asked.
2. **Build** — one milestone-sized step: implement + verify + update docs + commit, then hand back a summary, what to review (diffs), and what to playtest (feel). Never more than the next single step.
3. **Loop** — (growing over time) multi-step autonomous runs with verification as the brake. Escalate on genuine ambiguity, repeated failure, or taste calls — otherwise keep going.

Division of labor: **the human is the taste-oracle, scope-setter, and diff reviewer — not the regression detector.** Detection belongs to gates and tests. The hand-back criterion is "verification green", never "please check if it works".

## Conventions

- **Docs move with the work**: update `PLAN.md` statuses and any affected doc in the same commit as the change they describe.
- **One coherent step per commit**, structured message (what + why), matching the labs' history style.
- **Verify before commit**: in a lab, its gate green (`tools/check.sh`); for dreamer's own code, dreamer's gate (`tools/check.sh` — uv-managed pytest).
- **Skill library**: `skills/<name>/{knowledge,prompt}.md`. `knowledge.md` = the *why*, confidence-labeled (✅ PROVEN / ◐ PARTIAL / ☐ INTENT); `prompt.md` = the operating procedure, feedable to a fresh agent on any game. Keep both theme-agnostic and engine-general where possible. Distill only from proven lab work.
- **Cross-repo references** use relative paths (`../new-game/...`); the labs and dreamer travel together under one parent directory.
- **Scope guard**: 2D, jam-scale, depth-first. Resist adding breadth (new labs, new legs) while a leg is mid-flight.
