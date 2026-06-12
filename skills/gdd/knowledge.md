# GDD for Automated Game Development — Knowledge Base

What a game design document must contain — and how it must be shaped — to serve as the
**input to an automated build** (the dreamer pipeline). Derived from reviewing lab #1's
`GAME_DESIGN.md` against what its agent-driven build actually consumed, decided alone, or
had to discover later. That evidence is real but observed **once, interactively** — so
sections are labeled ◐ PARTIAL unless stated. Trial #1 (cold replication) upgrades or
refutes them.

Companion: `prompt.md` (same directory) — the human-in-the-loop co-authoring procedure.

---

## Why the GDD is special in this pipeline  ◐

The GDD is the pipeline's only purely human-authored input; everything downstream either
reads it or is derived from it. The lab finding: **the GDD's job is not to answer
everything — it is to make explicit *who* answers each open thing**: the human (now, while
authoring), the build (later, by measurement and feel-proxy), or nobody (deferred out of
scope). A GDD that hides its ambiguity stalls an autonomous build; one that quarantines
ambiguity lets sessions run without a human in the room.

## The one idea: every statement carries a decision status  ◐

Lab #1's GDD did this implicitly and it is why the build never stalled: "mechanics locked;
theme is a swappable placeholder" (header), "~20–40s, escalating" (ranged numbers),
**Deferred** markers inside tables, and a closing "Open questions / to tune later" section.
Make the vocabulary explicit:

- **LOCKED** — the agent must respect it (pillars, core loop, input scheme). Changing it is
  a design change: human decision, deliberate commit.
- **TUNABLE** — the agent decides within a stated range, by measurement or feel-proxy, and
  records what it picked. All gameplay numbers should default to TUNABLE.
- **OPEN** — unresolved; the agent must escalate before building anything on it.
- **DEFERRED** — explicitly out of scope; the agent must NOT build it (the scope fence).

## Required sections (the template)  ◐

Eleven sections. Lab-#1 evidence for each is noted; #10 is the one addition the lab's GDD
*lacked* and later work had to invent.

1. **Header block** — design status, engine + version, dimensionality/perspective, last
   updated. *(Scaffolding reads this directly — it becomes `project.godot`.)*
2. **Vision & pillars** — the fantasy in a paragraph, a **genre anchor** ("in the spirit of
   *Brotato*" — one comparable compresses pages of spec), and 3–5 pillars. Pillars are
   tie-breakers: lab decisions like the data-driven architecture and the no-aim input scheme
   trace straight to "depth is in numbers, not content" and "easy to learn".
3. **Scope contract** — what the completable v1 is (lab: "survive all 5 waves to win") and
   an explicit backlog fence. The win/lose definition must be **mechanically testable** —
   the future harness measures against it.
4. **Theme & art plan** — theme status (final / placeholder-swappable), candidates if open,
   and a **graybox commitment** (programmer art first). Lab evidence: this is what let the
   build never block on assets. For automated v1 builds this section is effectively LOCKED
   to graybox-first.
5. **Core loop** — a diagram plus a numbered walkthrough, with win/lose exits. **The most
   load-bearing section**: the milestone ladder is approximately a topological sort of this
   loop, and every system traces to an arrow in it.
6. **Player verbs & full input map** — the signature mechanic(s) and the complete control
   scheme, with a closure statement (lab: "That's the entire control scheme. No aim
   input."). Closure is what made M1 ambiguity-free.
7. **System rules** — per system (combat, progression, economy…), rules precise enough to
   implement, numbers as TUNABLE ranges. Subtle rules MUST be written down even when short:
   lab's one-sentence "XP and materials are decoupled" defined the entire economy and the
   harness later depended on it. If a rule lives only in someone's head, the build will
   invent a different one.
8. **Content inventories** — tables for everything enumerable (enemies, weapons, slots,
   stats) with role + one-line behavior, and DEFERRED markers for closure. These tables map
   1:1 to `.tres` data files.
9. **Progression structure** — the encounter/wave/level table with an intended **feel** per
   stage (lab: "Tutorial → Ramp → Mix → Pressure → Boss finale"). The feel column is the
   difficulty curve's prose ancestor.
10. **Difficulty & player intent**  ☐ INTENT — *not present in lab #1's GDD; added from
    eval-leg experience.* Who the intended player is and how hard it should feel (e.g.
    "medium: standing still dies, skilled play wins ~75% on the margin"). Lab #1 had to
    invent this target profile months later during tuning; stating it in the GDD hands the
    evaluation skill its target band on day one.
11. **Decision ledger** — the explicit OPEN + TUNABLE list (lab: §11 "Open questions / to
    tune later"). The quarantine pen for everything unresolved, each item tagged with who
    resolves it (human / measurement / post-prototype).

Optional but useful: architecture principles (else they land in the project's conventions
doc) and a draft milestone ladder (else the bootstrap derives one — lab #1 carried §10
inline and the build consumed it directly).

## Shape rules (how it must look)  ◐

- Markdown, numbered sections, stable anchors — build sessions cite "§7" across weeks.
- **Tables for anything enumerable**; one-line behaviors. Prose hides rules; tables don't.
- Numbers carry `~` and ranges unless LOCKED. False precision blocks measurement-led
  tuning; lab feel-tuning was one-line data commits (fire_rate 3.0→1.5, pickup 90→50)
  precisely because numbers were declared soft and lived in data.
- Status markers inline where the content is (**Deferred** in the table row, placeholder
  flags in the theme section), not only in the ledger.
- Systems language stays theme-agnostic; theme words appear only in the theme section.
  (Lab: code never says "cow" or "alien" — the GDD models that discipline.)
- Whole-document scale: lab evidence ≈ 230 lines for a jam-scale game. The GDD must be
  holdable in one read by the agent that builds from it.

## The conformance check (the GDD gate)  ◐

A GDD is *buildable* when:
- all 11 sections present (a thin honest section passes; a missing one fails);
- win/lose conditions are mechanically testable;
- every number is LOCKED or ranged-TUNABLE;
- every inventory table is closed (complete for v1, or rows marked DEFERRED);
- the input map has a closure statement;
- the backlog fence exists;
- no stray ambiguity outside the ledger (scan for "TBD", "maybe", "?", "we'll see").

Fail ⇒ back to authoring (`prompt.md`), not into the build.

## Anti-patterns  ◐

- ❌ Rules buried in prose paragraphs — extract them to bullets/tables.
- ❌ Precise numbers everywhere — false certainty that fights the tuning loop.
- ❌ Ambiguity scattered through sections instead of quarantined in the ledger.
- ❌ Theme welded into systems language (blocks the late-skin workflow).
- ❌ Speccing UX flows that are really deferred (lab's win/lose UX changed post-prototype;
  it should have been marked DEFERRED rather than implied).
- ❌ Padding sections to satisfy the checklist — the check wants closure, not volume.
