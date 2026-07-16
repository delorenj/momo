# Momo — Product Requirements Document (PRD, v2)

**Date:** 2026-07-16
**Author:** Momo (acting PM, on Jarad's behalf)
**Status:** Draft for build kickoff — **v2** (post adversarial review)
**Companion docs:** [product-brief.md](./product-brief.md) · [../../docs/architecture.md](../../docs/architecture.md) · [epics.md](./epics.md)

## 1. Overview

Momo is 33GOD's in-project **PM+EM orchestrator**. This PRD specifies the **promotion** of the proven `momo` skill into a **liftable, versioned component** (`@delorenj/momo`) that installs into a drivable CommonProject repo, plus the seams that later let its behavior render into any agent CLI and run autonomously as the Hermes twin.

**Design stance:** thin promotion, maximal reuse. The behavior already exists and is contract-correct; the requirements are mostly **packaging, prerequisites, and seams** — deliberately *minimal* for the MVP after review showed the first draft over-scoped it.

## 2. Revenue Gate (Pillar #2 — answer before build)

The MVP demo must run on a **revenue-bearing product's board**, not on MOMO's own board (a platform piece managing itself is a *statue* by Pillar #2). **If no revenue product is ready to pull on Momo, the pillar-consistent decision is to defer the promotion** and keep using the skill. This is the one input only the CEO supplies.

## 3. Goals / Non-goals

**Goals:** one-command install into a drivable repo; **zero behavior regression** vs. today's skill (proven, not asserted); Momo clears a slice of a **revenue** board; house-norm consistency.

**Non-goals (MVP):** generic master spec + fanout engine (→ E4, the 2nd call-site); MCP proxy server (→ E6); heartbeat/systemd twin + fleet absorption (→ E5); adapters beyond the proven Claude skill; public npm release.

## 4. Functional Requirements

### FR-5.0 — Board-drivability prerequisite *(new — the blocker the review found)*
A target repo is drivable **only** if the resolved provider has its access path present.
- **FR-5.0.1** For **plane/linear**, a `tp` adapter must exist at `<role_dir>/.scripts/lib/ticket-provider.sh` with `.project.json.agents{}` naming its `role_dir` — provisioned by a Hermes PM deploy or a standalone pjangler `tp` install (**Toad/pjangler action, not Momo** — boundary D6). Verified: `momo-board.sh` exits 2 otherwise.
- **FR-5.0.2** For **trello**, no `role_dir` is needed (bundled `trello.py`) — the friction-free first demo path.

### FR-1 — Skill promotion (SSOT)
Lift the proven skill (`SKILL.md`, `references/*`, `templates/*`, `scripts/{momo-board.sh,record-decision.py,momo-config.py,providers/trello.py}`) into `33GOD/momo` as SSOT, behavior unchanged **except** FR-6.1.
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

### FR-5 — Board bring-up & self-heal
- **FR-5.1** `board_id` self-heal: resolve by **exact** name via `tp`, backfill, record as a decision; fail loud on zero/multiple.
- **FR-5.2** All board writes via `momo-board.sh`→`tp`; comments/events signed `momo`. *(Seeding MOMO's own backlog is non-blocking housekeeping.)*

### FR-6 — Decision provenance (preserve type; parameterize actor)
- **FR-6.1** Preserve `record-decision.py`'s event **type** (`bloodbank.v1.repo.decision.recorded`), derived subject, and dual-sink (local JSONL + best-effort NATS) exactly. **Carve-out:** `actor.cli`/`actor.provider` (hardcoded `claude`/`anthropic` at line 124) are **parameterized** from the active carrier — the one place the skill is *not* lifted verbatim, required by the CLI-agnostic thesis.
- **FR-6.2** `basis[]` cites **process-pillar** slugs (`references/pillars.md`) **and/or** the 4 **product-pillar** slugs (`PILLARS.md`). Validation must accept process slugs (the board_id self-heal uses them).

### FR-7 — Memory (preserve; guard honcho later)
- **FR-7.1** Hindsight bank = `project_slug`, worktree-safe, shared with the Hermes twin; actor `momo`.
- **FR-7.2** For the deferred twin (E5), the Hermes adapter **neutralizes honcho** so only the shared Hindsight bank is used.

### FR-8 — Second CLI adapter (→ E4)
- **FR-8.1** Add one **file-render** dialect (OpenCode/Codex) from the unchanged master; the non-Claude carrier proves the `actor` parameterization (FR-6.1).

## 5. Non-Functional Requirements

- **NFR-1 Byte-identity with Hermes (scoped + tested).** Same `tp` path, 5 states, shared decision trail. Byte-identity holds via `tp` for **plane/linear**; **Trello diverges** (Momo `trello.py` vs Hermes `tp providers/trello.sh`) until consolidated. **Prove it** with a differential test (same board through both paths; assert identical) — not self-consistency. Reconcile the reconcile-**pass** definition into one source (2 live call-sites now).
- **NFR-2 Dependency-light glue** — stdlib Python3 + Bash; TS confined to the wrapper.
- **NFR-3 Secrets discipline** — `op inject` on `mise enter`; `PLANE_<WS>_API_KEY`→`PLANE_API_KEY`; nothing sensitive committed.
- **NFR-4 Contract fidelity** — Bloodbank types/subjects (5-token), `.project.json` fields, normalized states honored verbatim; no new schemas.
- **NFR-5 Idempotence & no-clobber** — install/fanout idempotent; generated copies never hand-edited.
- **NFR-6 Provider agnosticism** — resolved from `.project.json`; never hardcoded.
- **NFR-7 Versioning honesty** — `--version` from manifest/git tag.
- **NFR-8 Bias to reversible action** — destructive/paid/prod actions require explicit escalation.
- **NFR-9 No dead installs / no split-brain (executable, not advisory).** `momo doctor` is a **hard gate** enumerating all prereqs (python3, bash, `tp` adapter **or** trello creds for the resolved provider, `$BLOODBANK_HOME` reachable, provider keys present) and refuses "ready" until green. WIP=1 is enforced by a **real shared lock** (Momo takes the sentinel `flock` / honored `interactive-hold` marker) — not politeness. An **executable guard** forbids importing/spawning `plane-mcp-server` or bypassing `momo-board.sh` (enforces D5 from the moment the `momo-mcp` bin exists).

## 6. Epics (detail in [epics.md](./epics.md))

| # | Epic | MVP? | Pillar |
|---|---|---|---|
| **Gate** | Revenue-product pick (or defer) | ✅ input | #2 |
| **E0** | Prerequisites & board-drivability (`tp` adapter, `board_id` self-heal) | ✅ | #2 enabler |
| **E1** | Promote the skill (SSOT) — verbatim + 2 surgical changes; prove byte-identity | ✅ | #3 |
| **E2** | Minimal install + **demo on a revenue board** (front-loaded); doctor gate; shared lock | ✅ **demo** | #1 |
| **E3** | House-norm packaging (TS two-bin, versioning, clean `mise enter`) | ▫ post-demo | #4 |
| **E4** | Generic spec + fanout + 2nd adapter | ▫ post-MVP | #3 (2nd occurrence) |
| **E5** | Autonomous twin (Hermes adapter; honcho-off; heartbeat) | ⛔ gated | #1 gate |
| **E6** | MCP proxy (delegates to `tp`; 6 verbs; no `create_board`) | ⛔ gated | Rule of Three |

## 7. Acceptance (MVP definition of done)

`momo install` into a **drivable, revenue-product repo** materializes the proven skill; `momo doctor` gates prereqs green; the installed Momo **clears a real slice of that revenue board** (triage→delegate→review→`completed`) emitting a `decision.recorded` event to the shared trail — with behavior proven **byte-identical to Hermes** (differential test) and a real WIP=1 lock preventing split-brain. The sellable demo is recorded early against the existing skill and re-recorded against the installed component. (The circular "runs its own MOMO board" metric is dropped.)

## 8. Dependencies & assumptions

- **Reuse:** `33GOD/skills/momo`, `toad/src/fanout` (E4), `hermes-agent-template` (E5), `bloodbank` (schemas + stdlib publisher), pjangler `tp`.
- **Prereq (FR-5.0):** a `tp` adapter (Hermes/pjangler) for any plane/linear target — including MOMO's own repo (`agents:{}` today).
- **External gate:** seeding a live board / running on a revenue board is an outward action — on explicit go-live only.

---

_Generated as part of the Momo planning lifecycle (BMAD-style). v2 incorporates the adversarial-review findings._
