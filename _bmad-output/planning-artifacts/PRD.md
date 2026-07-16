# Momo — Product Requirements Document (PRD)

**Date:** 2026-07-16
**Author:** Momo (acting PM, on Jarad's behalf)
**Status:** Draft for build kickoff
**Companion docs:** [product-brief.md](./product-brief.md) · [../../docs/architecture.md](../../docs/architecture.md) · [epics.md](./epics.md)

## 1. Overview

Momo is 33GOD's in-project **PM+EM orchestrator**. This PRD specifies the **promotion** of the proven `momo` skill into a **liftable, versioned component** (`@delorenj/momo`) that installs into any pjangler CommonProject repo, plus the seams that let its behavior render into any agent CLI and (later) run autonomously as the Hermes twin.

**Design stance:** maximize reuse. The behavior already exists and is contract-correct; the requirements below are mostly about **packaging, distribution, and seams**, not new PM logic.

## 2. Goals / Non-goals

**Goals:** one-command install; zero behavior regression vs. today's skill; liftable into ≥2 repos and renderable into ≥2 CLI dialects; Momo runs its own MOMO board; house-norm consistency.

**Non-goals (MVP):** MCP proxy server; heartbeat/systemd autonomous twin; fleet absorption; adapters beyond Claude; public npm release. (All deferred — see brief §7.)

## 3. Functional Requirements

### FR-1 — Skill promotion (SSOT)
The proven skill (`SKILL.md`, `references/*`, `templates/*`, `scripts/{momo-board.sh,record-decision.py,momo-config.py,providers/trello.py}`) is lifted into the `33GOD/momo` repo as the component's **single source of truth**, unchanged in behavior.
- **FR-1.1** Resolve and document the SSOT-drift question (`skills/momo` vs. the stale `skillex` path BRAINDUMP cites) and record which is canonical.
- **FR-1.2** Verify byte-correctness against live contracts after the lift: decision event shape, `tp` op contract, 5 normalized states.
- **FR-1.3** Wire the pending `PILLARS.md` checklist row (Momo agent spec/soul **references** PILLARS, never forks).
- **FR-1.4** Correct `docs/` (architecture/index/overview) to reflect the as-built reality and the D5 Plane-MCP correction.

### FR-2 — Component wrapper & versioned package
A TS/Node package mirroring the **toad/pjangler two-bin skeleton**.
- **FR-2.1** `package.json` as `@delorenj/momo`, ESM, two bins (`momo` CLI + reserved `momo-mcp`), `@modelcontextprotocol/sdk` + `commander` + `zod`, `esbuild` build → `dist/`.
- **FR-2.2** mise tasks: `build`, `test`, `fanout`, plus the existing `version:*` managed block; `--version` derives from the manifest/git tag (never a hardcoded literal).
- **FR-2.3** The TS wrapper **shells out to** the Python/Bash glue (does not reimplement it); document the runtime deps (python3, bash).

### FR-3 — Generic agent spec (contract ⁄ personality split)
A CLI-agnostic master spec adopting the Hermes two-file topology.
- **FR-3.1** A `role.yaml`-shaped machine contract (repo, role/kind, agent_id, ticket_provider binding, bloodbank subjects/producer, memory bank = repo slug, model = inherit) — a **superset that projects onto** Hermes `role.yaml`.
- **FR-3.2** A `SOUL.md`-shaped personality/behavior file that **references `PILLARS.md`** (never inlines it) and carries the tone knob + Momo behavior contract.
- **FR-3.3** The generic spec is the **master**; all per-CLI copies are generated (never hand-edited).

### FR-4 — Fanout install + Claude adapter (MVP demo)
Lift Toad's fanout engine as the install/distribution mechanism.
- **FR-4.1** Extract Toad's `src/fanout/{engine.ts,targets.ts}` + adapters into a seam Momo consumes (shared lib or vendored-with-attribution; no second drifting fanout engine).
- **FR-4.2** Ship the **Claude Code skills-tree adapter** first (the dialect Toad already renders): `momo install <repo>` materializes the skill tree from the generic master.
- **FR-4.3** `momo fanout sync` regenerates all dialects from the master; `momo fanout check` is a CI drift gate (fails on hand-edited generated copies).
- **FR-4.4** Install is idempotent and repo-agnostic (resolves nearest-ancestor `.project.json`).

### FR-5 — Board bring-up & self-heal (dogfood enabler)
Momo must be able to run its **own** board.
- **FR-5.1** Implement/confirm the `board_id` self-heal flow: when `.project.json.ticket_provider.board_id` is empty, resolve by **exact** board name in the workspace, backfill it, and **record the backfill as a decision** (`data.basis` = pillar slugs). Never guess among near-duplicate boards.
- **FR-5.2** Seed this planning backlog (epics/stories) onto the MOMO Plane board.
- **FR-5.3** All board writes go through `momo-board.sh` → `tp`; comments/events signed `momo`.

### FR-6 — Decision provenance (already wired; preserve)
- **FR-6.1** Preserve `record-decision.py` exactly: type `bloodbank.v1.repo.decision.recorded`, dual-sink (local JSONL trail + best-effort NATS via bloodbank's stdlib publisher), slug from `.project.json`.
- **FR-6.2** Every consequential judgment call made by Momo (including `board_id` self-heal and scope decisions) is recorded with `basis[]` mapping to the 4 pillars.

### FR-7 — Memory (already wired; preserve)
- **FR-7.1** Hindsight bank = `project_slug`, worktree-safe resolution, shared with the Hermes twin; retain/recall as actor `momo`.
- **FR-7.2** Adopt the two-tier memory model (durable Hindsight + a session-start `MEMORY.md` mental model) when the runtime is defined.

### FR-8 — Second CLI adapter (seam validation)
- **FR-8.1** After the Claude adapter demos, add **one** more dialect (OpenCode or Codex or Hermes) to validate the generic-spec seam with a real second call-site (Rule of Three).

## 4. Non-Functional Requirements

- **NFR-1 Byte-identity with Hermes** — same board resolution path (`tp`), same 5 states / 7 ops, same shared decision trail (`_bmad-output/implementation-artifacts/bloodbank-events.jsonl`). No split-brain.
- **NFR-2 Dependency-light glue** — skill glue stays stdlib Python3 + Bash (drops into any repo with no heavy deps). TS wrapper confined to the component layer.
- **NFR-3 Secrets discipline** — 1Password `op inject` on `mise enter`; `PLANE_<WS>_API_KEY`→`PLANE_API_KEY` (X-API-Key), `PLANE_BASE` default `https://plane.delo.sh`; nothing sensitive committed.
- **NFR-4 Contract fidelity** — Bloodbank types/subjects, `.project.json` fields, and normalized states are honored verbatim; no new event schemas needed (reuse existing `repo.*`).
- **NFR-5 Idempotence & no-clobber** — install/fanout are idempotent; generated copies are never hand-edited (drift gate enforces).
- **NFR-6 Provider agnosticism** — provider resolved from `.project.json`, never hardcoded (Factory).
- **NFR-7 Versioning honesty** — `--version` derives from the manifest/git tag; add product manifests to `.mise/version-files.conf` once they exist.
- **NFR-8 Bias to reversible action** — destructive/paid/prod actions require explicit escalation, not silent execution (matches the skill's stop conditions).

## 5. Epics (detail in [epics.md](./epics.md))

| # | Epic | MVP? | Pillar driver |
|---|---|---|---|
| **E0** | Board bring-up & reconciliation (self-heal MOMO `board_id`, seed backlog) | ✅ enabler | #2 dogfood |
| **E1** | Promote the skill (SSOT) + correct docs | ✅ | #3 Rule of Three |
| **E2** | Component wrapper & versioned package (`@delorenj/momo`) | ✅ | #4 house norm |
| **E3** | Fanout install + Claude adapter (**demo milestone**) | ✅ | #1 shortest path |
| **E4** | Second CLI adapter (seam validation) | ▫ post-MVP | #3 Rule of Three |
| **E5** | Autonomous twin (heartbeat via Hermes adapter) | ⛔ deferred/gated | #1 (gate on revenue) |
| **E6** | MCP proxy server (delegates to `tp`, not Plane MCP) | ⛔ deferred/gated | Rule of Three (2nd consumer) |

## 6. Dependencies & assumptions

- **Reuse sources:** `33GOD/skills/momo` (skill), `33GOD/toad/src/fanout` (fanout engine + component skeleton), `hermes-agent-template` (spec topology, heartbeat — E5), `bloodbank` (schemas + stdlib publisher), pjangler `tp` adapter.
- **Assumption:** the `skills/momo` copy is the working SSOT (FR-1.1 confirms).
- **External gate:** seeding the live MOMO board (FR-5.2) is an outward action — created only on explicit go-live.

## 7. Acceptance (definition of done for the MVP)

`momo install` into a fresh CommonProject repo materializes the skill, `momo fanout check` passes, and the installed Momo runs a board loop (triage→delegate→review→clear) emitting a `decision.recorded` event — with behavior indistinguishable from today's hand-carried skill, and Momo's own MOMO board bootstrapped and seeded.

---

_Generated as part of the Momo planning lifecycle (BMAD-style)._
