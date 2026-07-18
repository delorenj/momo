# Momo — Product Requirements Document (PRD, v3)

**Date:** 2026-07-18
**Author:** Momo (acting PM, on Jarad's behalf)
**Status:** Lifecycle policy-client slice implemented; broader promotion remains gated — **v3**
**Companion docs:** [product-brief.md](./product-brief.md) · [../../docs/architecture.md](../../docs/architecture.md) · [epics.md](./epics.md)

## 1. Overview

Momo is 33GOD's in-project **PM+EM orchestrator**. This PRD specifies the **promotion** of the proven `momo` skill into a **liftable, versioned component** (`@delorenj/momo`) that installs into a drivable CommonProject repo, plus the seams that later let its behavior render into any agent CLI and run autonomously as the Hermes twin.

**Design stance:** thin promotion, maximal reuse. The PM/EM policy, delegation,
review, and decision-provenance behavior already exists. Direct provider
transitions are **legacy migration utilities**, not the lifecycle contract.
Momo becomes an intelligent client of the separate headless Lifecycle component.

**Approved authority boundary (2026-07-18):** Lifecycle alone owns versioned
spec/state, deterministic reconciliation, legal frontier, obligations, and
capability validation. Bloodbank owns canonical transport/contracts, Candystore
owns durable history/read models, PJangler owns project/bootstrap identity, and
Holocene renders authoritative state and submits high-level commands. Momo reads
Lifecycle's frontier, applies the Pillars to choose among legal work, delegates
and reviews, and submits idempotent intent. It never calculates or writes
lifecycle truth. The standalone Lifecycle authority, canonical Bloodbank
contracts, Candystore projection, and Momo client seam are implemented in the
current integration slice.

## 2. Revenue Gate (Pillar #2 — answer before build)

The MVP demo must run on a **revenue-bearing product's board**, not on MOMO's own board (a platform piece managing itself is a *statue* by Pillar #2). **If no revenue product is ready to pull on Momo, the pillar-consistent decision is to defer the promotion** and keep using the skill. This is the one input only the CEO supplies.

## 3. Goals / Non-goals

**Goals:** one-command install into a drivable repo; preserve the proven PM/EM
policy while replacing direct transitions with a versioned Lifecycle client;
Momo clears a legal slice of a **revenue** work frontier; house-norm consistency.

**Non-goals (MVP):** implementing Lifecycle inside Momo; treating the ticket
provider as lifecycle truth; generic master spec + fanout engine (→ E4, the 2nd
call-site); heartbeat/systemd twin + fleet absorption (→ E5); adapters beyond
the proven Claude skill; public npm release.

## 4. Functional Requirements

### FR-0 — Lifecycle client boundary *(approved major correction)*
- **FR-0.1** Resolve stable project identity through PJangler inputs, then read an
  authoritative Lifecycle snapshot containing lifecycle ID, `spec_version`,
  `state_version`, legal frontier, obligations, blockers, and capability grants.
- **FR-0.2** Apply Momo's business/process pillars only to rank and choose among
  actions present in the legal frontier. Pillars cannot legalize an action.
- **FR-0.3** Submit state-changing intent as an idempotent Bloodbank command with
  expected state version and capability context. Render accepted, rejected,
  stale, and unavailable results; never optimistically write lifecycle state.
- **FR-0.4** Submit observations, evidence, review verdicts, and decision
  provenance as inputs/events. A decision event audits reasoning; it does not
  authorize or enact a transition.
- **FR-0.5** Missing or stale projections and invalid grants block execution.
  `momo-board.sh`/`tp`/Trello transitions are explicitly migration-only and
  cannot satisfy target-state acceptance.

### FR-5.0 — Project and projection prerequisites
A target repo is drivable in the approved target only when PJangler identity,
Lifecycle availability/capability, and the provider projection are resolvable.
- **FR-5.0.1** For **plane/linear**, a `tp` adapter must exist at `<role_dir>/.scripts/lib/ticket-provider.sh` with `.project.json.agents{}` naming its `role_dir` — provisioned by a Hermes PM deploy or a standalone pjangler `tp` install (**Toad/pjangler action, not Momo** — boundary D6). Verified: `momo-board.sh` exits 2 otherwise.
- **FR-5.0.2** For **trello**, no `role_dir` is needed for the current bundled
  projection adapter. It is not a bypass around the Lifecycle command gate.
- **FR-5.0.3** `momo doctor` must reject target-ready status when the Lifecycle
  snapshot/command contract is unavailable or the caller lacks a grant.

### FR-1 — Skill promotion (SSOT)
Lift the proven skill (`SKILL.md`, `references/*`, `templates/*`,
`scripts/{momo-board.sh,record-decision.py,momo-config.py,providers/trello.py}`)
into `33GOD/momo` as SSOT. Preserve its PM/EM policy, delegation, review, and
provenance behavior; replace legacy state writes per FR-0 and parameterize the
actor per FR-6.1.
- **FR-1.1** Resolve SSOT-drift (`skills/momo` canonical; `skillex` path dead) and record it.
- **FR-1.2** After the lift, the operator's **global** installed skill is regenerated-from/symlinked-to the repo master — no second drifting copy.
- **FR-1.3** Preserve **both pillar tiers**: universal **process** pillars (`references/pillars.md`) and the 4 **product** pillars (`PILLARS.md`). Document the **safety-supremacy invariant** (process/safety pillars are never overridden by a product pillar).
- **FR-1.4** Correct `docs/` (architecture/index/overview) — enumerated in epics S1.6.

### FR-2 — Component wrapper & versioned package (Pillar #4 — *after* the demo)
Toad/pjangler two-bin skeleton wrapping the Python/Bash glue.
- **FR-2.1** `@delorenj/momo`, ESM, bins `momo` + reserved `momo-mcp`, `@modelcontextprotocol/sdk` + `commander` + `zod`, `esbuild`→`dist/`.
- **FR-2.2** mise `build`/`test`/`version:*`; `--version` from manifest/git tag; `package.json` in `.mise/version-files.conf`; clean `mise enter` (op inject resolves).
- **FR-2.3** `momo doctor` = **hard prereq gate** (see NFR-3/NFR-9); TS shells out to the glue (no reimplementation).

### FR-3 — Generic agent spec (→ E4, the 2nd call-site; NOT MVP)
- **FR-3.1** A `role.yaml`-shaped machine contract that **projects onto** Hermes `role.yaml` — validated against the real `role.yaml.jinja`. **The emitted decision type stays 5-token** (`bloodbank.v1.repo.decision.recorded`, slug in `data.repo`); repo/agent_id live only in **subscribe** subjects, never the emitted type.
- **FR-3.2** A `SOUL.md`-shaped file that **references `PILLARS.md`** (never inlines) + tone knob.
- **FR-3.3** The master is the only hand-edited source; generated copies carry a "do not edit" header.

### FR-4 — Install & fanout
- **FR-4.2 (MVP)** `momo install <repo>` drops the **proven Claude skills-tree directly** (no generic-master projection); idempotent; resolves nearest-ancestor `.project.json`; writes decisions to the exact shared `bloodbank-events.jsonl` trail the target's Hermes sentinel reads.
- **FR-4.1 (→ E4)** Extract/vendor Toad's fanout engine — correct manifest (`engine.ts + spec.ts + targets.ts + util/deterministic.ts + adapters/*`), a Toad golden test **first**, and a `loadSpec`↔master-schema reconciliation.
- **FR-4.3 (→ E4)** `momo fanout sync` / `fanout check` drift gate (meaningful once ≥2 dialects exist).

### FR-5 — Provider projection & binding repair
- **FR-5.1** `board_id` self-heal is a PJangler/bootstrap binding repair:
  resolve by exact name, backfill identity metadata, submit the observation, and
  record the judgment; fail loud on zero/multiple. It does not write Lifecycle.
- **FR-5.2** Target state changes use the Lifecycle command seam only. Provider
  adapters may read projections and post signed comments; direct transition
  support remains legacy migration behavior. *(Seeding MOMO's own backlog is
  non-blocking housekeeping.)*

### FR-6 — Decision provenance (preserve type; parameterize actor)
- **FR-6.1** Preserve `record-decision.py`'s event **type**
  (`bloodbank.v1.repo.decision.recorded`), derived subject, and dual-sink.
  Parameterize `actor.cli`/`actor.provider` from the active carrier. This is an
  intentional provenance change alongside, but distinct from, the FR-0
  lifecycle-client correction.
- **FR-6.2** `basis[]` cites **process-pillar** slugs (`references/pillars.md`) **and/or** the 4 **product-pillar** slugs (`PILLARS.md`). Validation must accept process slugs (the board_id self-heal uses them).

### FR-7 — Memory (preserve; guard honcho later)
- **FR-7.1** Hindsight bank = `project_slug`, worktree-safe, shared with the Hermes twin; actor `momo`.
- **FR-7.2** For the deferred twin (E5), the Hermes adapter **neutralizes honcho** so only the shared Hindsight bank is used.

### FR-8 — Second CLI adapter (→ E4)
- **FR-8.1** Add one **file-render** dialect (OpenCode/Codex) from the unchanged master; the non-Claude carrier proves the `actor` parameterization (FR-6.1).

## 5. Non-Functional Requirements

- **NFR-1 One authority across Momo and Hermes.** Both clients read the same
  Lifecycle snapshot and submit the same command contract. Provider-adapter
  differential tests remain useful for projection parity, but adapter byte
  identity is not lifecycle authority.
- **NFR-2 Dependency-light glue** — stdlib Python3 + Bash; TS confined to the wrapper.
- **NFR-3 Secrets discipline** — `op inject` on `mise enter`; `PLANE_<WS>_API_KEY`→`PLANE_API_KEY`; nothing sensitive committed.
- **NFR-4 Contract fidelity** — Bloodbank types/subjects, `.project.json`
  identity, Lifecycle IDs/versions/frontier/grants, and registered schemas are
  honored verbatim. Lifecycle commands/events require new canonical schemas.
- **NFR-5 Idempotence & no-clobber** — install/fanout idempotent; generated copies never hand-edited.
- **NFR-6 Provider agnosticism** — resolved from `.project.json`; never hardcoded.
- **NFR-7 Versioning honesty** — `--version` from manifest/git tag.
- **NFR-8 Bias to reversible action** — destructive/paid/prod actions require explicit escalation.
- **NFR-9 No dead installs / no split-brain.** `momo doctor` is a hard
  gate over local prerequisites, PJangler identity, Bloodbank access, Lifecycle
  availability/schema compatibility, provider projection, and capability grant.
  Command idempotency plus expected-state-version checks are authoritative;
  local WIP locks remain an additional worker-duplication guard.

## 6. Epics (detail in [epics.md](./epics.md))

| # | Epic | MVP? | Pillar |
|---|---|---|---|
| **Gate** | Revenue-product pick (or defer) | ✅ input | #2 |
| **E0** | Lifecycle-client prerequisite, projection access, and binding repair | ✅ dependency gate | #2 enabler |
| **E1** | Promote the policy skill; preserve provenance and prove one Lifecycle authority | ✅ | #3 |
| **E2** | Minimal install + revenue-product Lifecycle-client demo; doctor gate; shared lock | ✅ **demo** | #1 |
| **E3** | House-norm packaging (TS two-bin, versioning, clean `mise enter`) | ▫ post-demo | #4 |
| **E4** | Generic spec + fanout + 2nd adapter | ▫ post-MVP | #3 (2nd occurrence) |
| **E5** | Autonomous twin (Hermes adapter; honcho-off; heartbeat) | ⛔ gated | #1 gate |
| **E6** | MCP proxy (delegates to `tp`; 6 verbs; no `create_board`) | ⛔ gated | Rule of Three |

## 7. Acceptance (MVP definition of done)

`momo install` into a revenue-product repo materializes the proven policy client;
`momo doctor` gates prerequisites green; Momo reads a versioned Lifecycle
snapshot, selects work from its legal frontier, delegates and reviews, submits
idempotent intent/evidence, and renders the authoritative accepted or rejected
result. A `decision.recorded` event preserves reasoning without acting as the
transition. Momo and Hermes demonstrate one authority and no duplicate commands.
The policy-client portion of this acceptance is implemented and exercised
against the standalone Lifecycle service. Install/doctor packaging, the shared
Momo/Hermes WIP lock, and a revenue-product demo remain future acceptance work.

## 8. Dependencies & assumptions

- **Reuse:** the synchronized `momo/skill` and `33GOD/skills/momo`,
  `toad/src/fanout` (E4), `hermes-agent-template` (E5), Bloodbank
  transport/contracts, PJangler identity, and the standalone Lifecycle client
  contract.
- **Prereq (FR-5.0):** a `tp` adapter (Hermes/pjangler) for any plane/linear target — including MOMO's own repo (`agents:{}` today).
- **External gate:** seeding a live board / running on a revenue board is an outward action — on explicit go-live only.

---

_Generated as part of the Momo planning lifecycle (BMAD-style). v3 incorporates
the approved 2026-07-18 lifecycle-authority correction and records the
implemented policy-client vertical slice._
