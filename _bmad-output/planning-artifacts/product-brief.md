# Momo — Product Brief

**Date:** 2026-07-16
**Author:** Momo (acting PM, on Jarad's behalf)
**Status:** Draft for build kickoff
**Sources:** BRAINDUMP.md, PILLARS.md, and a 4-investigator grounding pass (as-built skill, Hermes reference, MCP landscape, ecosystem fit)

## 1. One-liner

Promote the **proven `momo` skill** into a **liftable, versioned 33GOD component** that installs its PM/EM orchestrator into any CommonProject repo with **one command** — reusing what already works instead of rebuilding it.

## 2. The situation (reality, not the BRAINDUMP aspiration)

Momo is **already real and working today** — but as a pure Claude Code **skill** at `~/code/33GOD/skills/momo` (1 `SKILL.md` + 6 references + 3 templates + 3 stdlib scripts). It already:

- runs the full manual PM loop (triage → refine → delegate-to-subagent → spec gate → quality gate → adversarial review → close gate → record decision),
- is **provider-agnostic** (Plane/Linear via the pjangler `tp` adapter; Trello via a bundled stdlib adapter + `.momo/config.json` lane map),
- **never edits code** (every change is delegated to a subagent),
- **emits canonical Bloodbank decision events** (`bloodbank.v1.repo.decision.recorded`, dual-sink local JSONL + best-effort NATS),
- shares one Plane board and one Hindsight bank (per repo) with the autonomous **Hermes PM**, honoring a shared WIP=1.

What does **not** exist: any compiled component, MCP server, generic agent spec, per-CLI adapters, or heartbeat service. Those are BRAINDUMP *aspirations*, and the `momo` **repo** (`33GOD/momo`) is a bare pjangler scaffold + doctrine + docs — **zero product code**.

> **Therefore this is a promotion/packaging job, not a greenfield build.** The Rule of Three is satisfied: Momo shipped concrete as a skill, got used and proven, and is now (second occurrence) earning its extraction into a reusable component.

## 3. Problem / opportunity

Today, using Momo on a new project means hand-carrying a skill and its glue. The opportunity: make Momo a **one-command-installable, versioned, drift-checked component** so every 33GOD project gets a consistent PM/EM orchestrator for free — the same way pjangler and toad are components. This hardens the single most reused piece of Jarad's solo-dev workflow (the thing that manages *all* his products).

## 4. Users

- **Primary:** Jarad (solo operator/CEO) — drives Momo interactively to run project boards and delegate implementation.
- **Secondary (same identity, different trigger):** the autonomous **Hermes PM** twin — the same reconcile loop fired by a timer instead of a human. Momo and Hermes share board + memory bank.
- **Tertiary (future):** any agent CLI (OpenCode, Codex, Kimi, Gemini) via generated adapters.

## 5. Goals & success metrics

| Goal | Success metric |
|---|---|
| One-command install | `momo install` drops the skill into any CommonProject repo; `momo fanout check` passes as a CI drift gate |
| Zero behavior regression | The installed component triages/delegates/reviews/clears a board and emits decision events **identically** to today's skill |
| Liftable (Pillar #3) | Momo installs into a *second* repo with no surgery; the generic spec renders into ≥2 CLI dialects |
| Dogfood proof (Pillar #2) | Momo clears a real slice of a **revenue product's** board (the circular "runs its own MOMO board" metric is dropped) |
| No split-brain (NFR) | On a repo with a live Hermes PM, Momo and Hermes coexist under a **real shared lock** — no board thrash (proven, not asserted) |
| Consistency (Pillar #4) | Component matches the house norm (toad/pjangler two-bin TS skeleton; Python/Bash glue lifted verbatim) — *post-demo* |

## 6. MVP scope (the first sellable/demoable slice) — *lean, demo-first*

> **Revised (v2, post-review):** the first draft over-scoped this. The review showed the
> generic-spec + fanout machinery is a Rule-of-Three violation on the *first* call-site — so
> the MVP ships the **proven Claude skill directly** and defers that machinery to the 2nd adapter.

**In:** provision the board-drivability prerequisite (a `tp` adapter for plane/linear, or a
Trello board); promote the proven skill as SSOT (verbatim except parameterizing the decision
`actor.cli`); a **minimal `momo install`** that drops the proven Claude skills-tree into a
target repo; a `momo doctor` prereq gate; a real WIP=1 lock; and the demo **recorded first**.

**Demo:** *point Momo at a **revenue product's** repo → one command installs it → watch it
triage, delegate, review, and clear a real slice of that board while emitting decision events.*
(The behavior already exists; the MVP makes it installable, safe alongside Hermes, and proven.)

**Explicitly NOT in the MVP** (moved to E4, the honest 2nd occurrence): the generic master
spec, Toad's fanout engine extraction, and the TS house-norm packaging — all *after* the demo.

## 7. Explicitly out of scope for MVP (deferred, Rule-of-Three-gated)

- **MCP proxy server** over Plane+Trello — `momo-board.sh` already covers board ops with one real driver; wait for a second consumer. **And it must delegate to `tp`/`trello.py`, never to the Python Plane MCP** (that path desyncs from Hermes).
- **Heartbeat / systemd autonomous twin** — validate the manual loop first; when built, **lift from Hermes** (`continuous-ticket-sentinel`) rather than inventing. Gate on a revenue product needing autonomy.
- **Absorbing the Hermes fleet** — BRAINDUMP's end-state ("Hermes PM becomes one deployment of generic Momo"). Momo ships a **Hermes adapter** later; the fleet stays separate for now.
- **Adapters beyond Claude** (OpenCode/Codex/Kimi/Gemini/Hermes) — one first, then a second to validate the seam.
- **npm public distribution** — internal dogfood first; package structured for publish, release deferred.

## 8. Non-negotiable constraints (locked contracts)

1. **Never edits code** — Momo delegates every change to a subagent. The component must not add code-editing to Momo itself.
2. **Board access only via `momo-board.sh` → `tp` adapter** — never direct Plane/Trello API, never `project-lifecycle`'s plane path (desyncs from Hermes). Normalized **5 states**; Momo speaks **6 of the `tp` contract's 7 ops** (`create_board` is reserved to Toad/pjangler per D6).
3. **Decision event = `bloodbank.v1.repo.decision.recorded`** — exactly 5 tokens, repo slug in `data.repo` (the 6-token form is rejected). Provider/CLI names are banned in the type.
4. **Hindsight bank = `project_slug`**, shared with the Hermes twin — never split by agent identity.
5. **`PILLARS.md` is referenced, never forked** — wire the pending "Momo agent spec/soul" checklist row; `basis[]` slugs on decisions map to the pillars.
6. **WIP=1 shared with Hermes** — check sentinel state before dispatch; sign board comments/events as `momo`.
7. **Two-language norm** — don't rewrite working Python/Bash in TS; wrap it.
8. **Board-drivability prerequisite** — for plane/linear, a `tp` adapter must be installed in
   the target repo's `role_dir` (via Hermes/pjangler — *not* Momo); `momo-board.sh` exits 2
   without it. Trello needs none. "Liftable without surgery" is gated by `momo doctor`, which
   hard-fails until all prereqs (python3, bash, adapter/creds, `$BLOODBANK_HOME`, keys) are green.
9. **Two-tier pillars** — decisions cite **process** pillars (`references/pillars.md`) and/or
   **product** pillars (`PILLARS.md`); process/safety pillars are never overridden by a product one.

## 9. Key decisions made on the CEO's behalf (with basis)

- **D1 Promotion, not rewrite** — lift the proven glue verbatim. *(Rule of Three; avoid re-introducing contract bugs.)*
- **D2 Language: Python/Bash glue + TS/Node wrapper.** *(Pillar #4 house norm; Pillar #3 reuse.)*
- **D3 MVP = one-command install via lifted Toad fanout + Claude adapter.** *(Pillar #1 shortest path to demo.)*
- **D4 Defer MCP proxy + heartbeat.** *(Rule of Three; don't abstract on the first occurrence.)*
- **D5 Never proxy the Python Plane MCP** — delegate to `tp`. *(Correctness; board-awareness SSOT.)*
- **D6 Toad births/audits; Momo runs the board** — no scope overlap. *(One-source-of-truth per component.)*
- **D7 Hermes stays separate; Momo ships a Hermes adapter later; dogfood before distribution.** *(Pillar #1 + #2.)*

## 10. Risks

- **Rewrite-instead-of-promote** → re-introduces contract bugs and wastes the earned abstraction. *Mitigate: lift Python/Bash verbatim.*
- **Statue risk (Pillar #2)** → building the component with no revenue product pulling on it. *Mitigate: sequence the backlog to dogfood Momo on the current tip-of-the-spear product; keep MVP cheap by reusing.*
- **Fanout duplication** → forking a second spec-fanout engine instead of lifting Toad's. *Mitigate: extract Toad's engine into a shared seam.*
- **Board desync** → any divergent board-resolution path (Plane MCP, project-lifecycle plane json) breaks byte-identity with Hermes. *Mitigate: single seam = `momo-board.sh`/`tp`.*
- **Autonomy-first scope creep** → building the heartbeat twin before validating the manual loop. *Mitigate: manual slice first.*

## 11. The one gating decision only the CEO can make

**Which revenue-bearing product does Momo dogfood first — or is there none yet?** This is now
a **hard gate on the build, not a footnote** (the adversarial review showed the whole MVP,
scoped to MOMO-on-MOMO, is a statue by Pillar #2's own definition). Two branches:

- **A product X is ready** → the E2 demo runs on **X's board**; the promotion is justified
  (it hardens the PM of a real revenue product). Everything else in this brief I've decided.
- **No product is ready to pull on Momo yet** → the pillar-consistent call is to **defer the
  promotion** and keep using the skill as-is (Rule of Three: don't build the abstraction on
  spec). The plan stays on the shelf, ready, costing nothing.

*(Everything else — language, sequencing, scope, contracts — I've decided on your behalf. This
is the single business-pipeline input I can't derive from the code or the doctrine.)*

---

_Generated as part of the Momo planning lifecycle (BMAD-style)._
