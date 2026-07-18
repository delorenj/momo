# Momo — Product Brief

**Date:** 2026-07-18
**Author:** Momo (acting PM, on Jarad's behalf)
**Status:** Approved boundary correction; target implementation gated
**Sources:** BRAINDUMP.md, PILLARS.md, and a 4-investigator grounding pass (as-built skill, Hermes reference, MCP landscape, ecosystem fit)

## 1. One-liner

Promote the **proven `momo` skill** into a liftable, versioned PM/EM
process-manager that installs into any CommonProject repo, selects among legal
work exposed by Lifecycle, and submits auditable intent without owning lifecycle
truth.

## 2. The situation (reality, not the BRAINDUMP aspiration)

Momo is **already real and working today** — but as a pure Claude Code **skill** at `~/code/33GOD/skills/momo` (1 `SKILL.md` + 6 references + 3 templates + 3 stdlib scripts). It already:

- runs the full manual PM loop (triage → refine → delegate-to-subagent → spec gate → quality gate → adversarial review → close gate → record decision),
- is **provider-agnostic** (Plane/Linear via the pjangler `tp` adapter; Trello via a bundled stdlib adapter + `.momo/config.json` lane map),
- **never edits code** (every change is delegated to a subagent),
- **emits canonical Bloodbank decision events** (`bloodbank.v1.repo.decision.recorded`, dual-sink local JSONL + best-effort NATS),
- shares one provider board and one Hindsight bank (per repo) with the autonomous
  **Hermes PM**, honoring a shared WIP=1.

The current skill also writes provider transitions directly. That behavior is
real but **legacy**: it must be replaced by idempotent commands to the separate
Lifecycle authority. A provider board is a projection, not the source of legal
state.

What does **not** exist: any compiled component, MCP server, generic agent spec, per-CLI adapters, or heartbeat service. Those are BRAINDUMP *aspirations*, and the `momo` **repo** (`33GOD/momo`) is a bare pjangler scaffold + doctrine + docs — **zero product code**.

> **Therefore this is a promotion/packaging job, not a greenfield build.** The Rule of Three is satisfied: Momo shipped concrete as a skill, got used and proven, and is now (second occurrence) earning its extraction into a reusable component.

## 3. Problem / opportunity

Today, using Momo on a new project means hand-carrying a skill and its glue, and
its direct provider transitions duplicate lifecycle policy. The opportunity is a
one-command-installable, versioned PM/EM client that preserves Momo's business
judgment while one headless Lifecycle component provides deterministic state,
frontier, obligations, and capability validation.

## 4. Users

- **Primary:** Jarad (solo operator/CEO) — uses Momo interactively to manage
  project work and delegate implementation.
- **Secondary (same identity, different trigger):** the autonomous **Hermes PM**
  twin — the same PM/EM policy client fired by a timer instead of a human. Momo
  and Hermes share the authoritative client contract, projection, and memory bank.
- **Tertiary (future):** any agent CLI (OpenCode, Codex, Kimi, Gemini) via generated adapters.

## 5. Goals & success metrics

| Goal | Success metric |
|---|---|
| One-command install | `momo install` drops the skill into any CommonProject repo; `momo fanout check` passes as a CI drift gate |
| Policy continuity | The installed component preserves triage, prioritization, delegation, review, and decision provenance while state changes move to Lifecycle commands |
| Liftable (Pillar #3) | Momo installs into a *second* repo with no surgery; the generic spec renders into ≥2 CLI dialects |
| Dogfood proof (Pillar #2) | On a revenue product, Momo selects legal work, delegates/reviews, submits intent/evidence, and renders Lifecycle's authoritative result |
| One lifecycle authority | Momo and Hermes read one versioned snapshot and submit idempotent commands; neither writes provider state as truth |
| Consistency (Pillar #4) | Component matches the house norm while preserving proven policy glue and replacing legacy state writes — *post-demo* |

## 6. MVP scope (the first sellable/demoable slice) — *lean, demo-first*

> **Revised (v3):** the first draft over-scoped this. The review showed the
> generic-spec + fanout machinery is a Rule-of-Three violation on the *first* call-site — so
> the MVP ships the **proven Claude skill directly** and defers that machinery to the 2nd adapter.

**In:** resolve PJangler identity and provider projection; promote the proven
policy/delegation/review skill as SSOT; replace direct state writes with the
Lifecycle client; parameterize decision actor identity; add a minimal install,
hard doctor gate, WIP=1 lock, and target demo.

**Target demo:** *point Momo at a revenue product → fetch the authoritative
Lifecycle snapshot/frontier → choose legal work using the Pillars → delegate and
review → submit intent/evidence → render the authoritative result while emitting
decision provenance.* The standalone Lifecycle service and this client seam do
not exist yet, so the target demo is gated rather than represented as current.

**Explicitly NOT in the MVP** (moved to E4, the honest 2nd occurrence): the generic master
spec, Toad's fanout engine extraction, and the TS house-norm packaging — all *after* the demo.

## 7. Explicitly out of scope for MVP (deferred, Rule-of-Three-gated)

- **MCP server** — wait for a second consumer. Its target surface is a thin
  Lifecycle snapshot/intent client; provider adapters remain read/migration
  projections rather than state-changing backends.
- **Heartbeat / systemd autonomous twin** — validate the manual loop first; when built, **lift from Hermes** (`continuous-ticket-sentinel`) rather than inventing. Gate on a revenue product needing autonomy.
- **Absorbing the Hermes fleet** — BRAINDUMP's end-state ("Hermes PM becomes one deployment of generic Momo"). Momo ships a **Hermes adapter** later; the fleet stays separate for now.
- **Adapters beyond Claude** (OpenCode/Codex/Kimi/Gemini/Hermes) — one first, then a second to validate the seam.
- **npm public distribution** — internal dogfood first; package structured for publish, release deferred.

## 8. Non-negotiable constraints (locked contracts)

1. **Never edits code** — Momo delegates every change to a subagent. The component must not add code-editing to Momo itself.
2. **Lifecycle state only through Lifecycle commands.** Momo reads a versioned
   snapshot/frontier and submits idempotent intent with expected state version and
   capability context through canonical Bloodbank contracts. `momo-board.sh` →
   `tp`/Trello remains a legacy provider-projection path, never target authority.
3. **Decision event = `bloodbank.v1.repo.decision.recorded`** — exactly 5 tokens, repo slug in `data.repo` (the 6-token form is rejected). Provider/CLI names are banned in the type.
4. **Hindsight bank = `project_slug`**, shared with the Hermes twin — never split by agent identity.
5. **`PILLARS.md` is referenced, never forked** — wire the pending "Momo agent spec/soul" checklist row; `basis[]` slugs on decisions map to the pillars.
6. **One authority shared with Hermes** — both clients use the same Lifecycle
   snapshot/command contract. Keep WIP=1 as an additional dispatch guard; sign
   comments/events as `momo`.
7. **Two-language norm** — don't rewrite working Python/Bash in TS; wrap it.
8. **Drivability prerequisite** — PJangler identity, provider projection,
   Bloodbank transport, Lifecycle schema compatibility/availability, and a
   capability grant must all resolve. `momo doctor` hard-fails target readiness
   until every prerequisite is green.
9. **Two-tier pillars** — decisions cite **process** pillars (`references/pillars.md`) and/or
   **product** pillars (`PILLARS.md`); process/safety pillars are never overridden by a product one.

## 9. Key decisions made on the CEO's behalf (with basis)

- **D1 Promotion, not rewrite** — preserve proven business policy, delegation,
  review, and provenance; adapt the state seam deliberately. *(Rule of Three.)*
- **D2 Language: Python/Bash glue + TS/Node wrapper.** *(Pillar #4 house norm; Pillar #3 reuse.)*
- **D3 MVP = minimal direct install of the corrected Claude policy skill; fanout
  stays deferred to E4.** *(Pillar #1 shortest path to target demo.)*
- **D4 Defer MCP proxy + heartbeat.** *(Rule of Three; don't abstract on the first occurrence.)*
- **D5 Never create a second lifecycle writer** — provider adapters are
  projections/migration aids; target transitions are Lifecycle commands.
- **D6 PJangler births/binds; Lifecycle reconciles; Momo manages process** —
  Momo selects legal work, delegates, reviews, and submits intent.
- **D7 Hermes stays separate; Momo ships a Hermes adapter later; dogfood before distribution.** *(Pillar #1 + #2.)*
- **D8 Decision events audit reasoning only.** They never authorize or enact a
  lifecycle transition.

## 10. Risks

- **Rewrite-instead-of-promote** → re-introduces contract bugs and wastes the
  earned abstraction. *Mitigate: preserve proven non-state behavior and isolate
  the required Lifecycle-client change.*
- **Statue risk (Pillar #2)** → building the component with no revenue product pulling on it. *Mitigate: sequence the backlog to dogfood Momo on the current tip-of-the-spear product; keep MVP cheap by reusing.*
- **Fanout duplication** → forking a second spec-fanout engine instead of lifting Toad's. *Mitigate: extract Toad's engine into a shared seam.*
- **Lifecycle split-brain** → direct provider writes from Momo/Hermes can diverge
  from deterministic truth. *Mitigate: one Lifecycle command seam with versions,
  idempotency, grants, and authoritative projections.*
- **Missing authority service** → the tested Bloodbank controller is only an
  embryo; outbox publication and schemas drift. *Mitigate: gate the target demo
  on extraction, history migration, contract closure, and rollback evidence.*
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

Regardless of product choice, no target lifecycle demo runs until the Lifecycle
component and canonical client contracts pass their implementation gates.

*(Everything else — language, sequencing, scope, contracts — I've decided on your behalf. This
is the single business-pipeline input I can't derive from the code or the doctrine.)*

---

_Generated as part of the Momo planning lifecycle (BMAD-style). Updated for the
approved 2026-07-18 authority correction; no Lifecycle implementation is claimed._
