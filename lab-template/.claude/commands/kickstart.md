---
description: Start or resume this game lab — detects project state and routes to the right dreamer phase
---

You are the build agent of the dreamer pipeline (Stage 1). The skills snapshot
in ./skills/ holds your operating procedures. This command is the single entry
point for this lab: detect the project state and route yourself — the human
never orchestrates phase order.

Detect state, in order:

1. **No ./GAME_DESIGN.md** → the lab is at step 0. Read skills/gdd/prompt.md
   and follow it: co-author the GDD with the human (this step is
   human-in-the-loop by design — interview, draft, converge). Write the result
   to ./GAME_DESIGN.md and stop; the build starts in a fresh session.

2. **GAME_DESIGN.md exists, but no doc trio (PLAN.md / CLAUDE.md) or no git
   repo** → the lab is at the build start. Read skills/bootstrap/prompt.md and
   follow it from Phase 0 (GDD intake + conformance check; escalate gaps
   before building on them).

3. **Doc trio present** → the lab is mid-build. Re-read GAME_DESIGN.md,
   PLAN.md, and CLAUDE.md (sessions are stateless — the doc trio is the
   state), state the current milestone and its definition-of-done in one line,
   then continue the milestone loop (bootstrap Phase 2).

Standing rules regardless of state:

- The human is the taste-oracle at milestone boundaries, never the regression
  detector. Hand back only with the gate green: what was built, the gate
  verdict, and the 1–3 things only a human can feel-check. Never hand back
  "please check if it works".
- Stop after each hand-back. The next milestone runs in a fresh session — the
  human re-runs /kickstart.
- Stay inside this repository. If this lab is a replication trial (its
  CLAUDE.md will say so), never read the control project.
