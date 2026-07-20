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
- **Monorepo layout**: dreamer's Python is a **uv workspace**. The repo root is a *virtual* workspace root (no product code, just `[tool.uv.workspace]` + a shared `dev` dependency-group). Product packages live under `packages/<name>/`, each an isolated package using the **src layout** (`src/<import_name>/`, uv/PyPA convention — source is importable only when installed, never via CWD) with its own `pyproject.toml`, `tests/`, and README. First member: `packages/asset-pipeline/` (imports as `asset_pipeline`). `tools/check.sh` gates the whole workspace (`uv sync --all-packages` + pytest).
- **Skill library**: `skills/<name>/{knowledge,prompt}.md`. `knowledge.md` = the *why*, confidence-labeled (✅ PROVEN / ◐ PARTIAL / ☐ INTENT); `prompt.md` = the operating procedure, feedable to a fresh agent on any game. Keep both theme-agnostic and engine-general where possible. Distill only from proven lab work.
- **Cross-repo references** use relative paths (`../new-game/...`); the labs and dreamer travel together under one parent directory.
- **Lab starter kit**: new labs start via `tools/bootstrap_game.sh <dir>` — it snapshots `skills/` plus a state-detecting `/kickstart` command (`lab-template/.claude/`) into the lab. Labs run from their snapshot, never from live dreamer paths (isolation for cold tests, provenance for grading); skill lessons fold back into dreamer's copies after the run.
- **Model routing**: dreamer-level work (design, skill distillation, grading) runs on Fable/Opus; lab build sessions run on Sonnet (pinned by the kit's `.claude/settings.json`). One session per milestone — end at the hand-back; the next session re-orients from the lab's doc trio.
- **Scope guard**: 2D, jam-scale, depth-first. Resist adding breadth (new labs, new legs) while a leg is mid-flight.
