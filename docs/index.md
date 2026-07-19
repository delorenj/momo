# Momo Documentation Index

**Type:** Monolith (pjangler CommonProject) — agentic PM/EM component
**Primary Language (decided):** Python3-stdlib + Bash (proven policy glue, with corrected Lifecycle seam) · TypeScript/Node (component wrapper, toad norm)
**Architecture:** Modular, adapter-based, provider-agnostic
**Status:** Implemented Lifecycle policy-client and durable obligation-actor slices; broader promotion remains future work
**Last Updated:** 2026-07-19
**Forward plan:** [product-brief](../_bmad-output/planning-artifacts/product-brief.md) · [PRD](../_bmad-output/planning-artifacts/PRD.md) · [epics](../_bmad-output/planning-artifacts/epics.md)

## Project Overview

**Momo** is 33GOD's PM/EM process-manager. It reads the authoritative
Lifecycle snapshot/frontier, uses [The Pillars](../PILLARS.md) to choose among
legal actions, delegates all code changes, independently reviews evidence, and
submits auditable intent. It never calculates or writes lifecycle truth.

This repo is the **promotion target**: the **fully-working skill** at `~/code/33GOD/skills/momo`
is being formalized into a reusable, versioned component (packaged skill + generic agent spec
+ fanout adapters; MCP proxy and heartbeat **deferred**). The repo now contains
the tested Lifecycle policy client and named-durable execution worker under
`skill/scripts/`.

The separate Lifecycle authority and canonical Bloodbank contracts are
implemented. Momo's client reads the Candystore projection and emits only
canonical Bloodbank commands. Direct `tp`/Trello transitions remain legacy
migration utilities and are not invoked by the authoritative workflow.

## Quick Reference

- **Repository Type:** Monolith (single `pjangler` CommonProject repo)
- **Entry Points:** `skill/scripts/lifecycle_client.py`, `skill/scripts/obligation_worker.py`, and `mise.toml`
- **Architecture Pattern:** Lifecycle client/facade + Adapter (per CLI/ticket-board provider) + Strategy/Factory + scheduled actor-work policy loop
- **Ticket Board:** Plane, workspace `33god`, identifier `MOMO` (`state: planned`)
- **Memory:** Hindsight, one bank per project (`momo` bank)
- **Events:** Bloodbank (NATS/Dapr/JetStream) — canonical schemas/transport, durable invocation delivery, and completion PubAck/dedup
- **Secrets:** 1Password via `op inject -i .env.op > .env`
- **Versioning:** git tags (mise-versioning)

## Generated Documentation

### Core Documentation

- [Project Overview](./project-overview.md) — Executive summary and high-level architecture
- [Source Tree Analysis](./source-tree-analysis.md) — Annotated directory structure (signal vs. framework noise)
- [Architecture](./architecture.md) — Intended architecture, current reality, the gap, and GoF pattern mapping
- [Development Guide](./development-guide.md) — Tooling, secrets, versioning, planning workflow, and known scaffold gaps

### Deferred surfaces

The policy client and bounded durable obligation actor are implemented and
tested. The following broader product surfaces remain deferred:

- Component Inventory — *(planned components are catalogued in [architecture.md §4](./architecture.md#4-component-breakdown))*
- API Contracts — *(the intended MCP tool surface is described in [architecture.md §4.2](./architecture.md#42-mcp-server-provider-proxy)) — To be generated when the MCP server is built*
- Data Models — *(Lifecycle owns state; target Momo consumes versioned projections and retains Hindsight/decision provenance)*
- Deployment Guide — *(intended heartbeat/systemd deployment sketched in [architecture.md §12](./architecture.md#12-deployment-intended)) — To be generated when the service exists*

## Source Documents (product signal)

- [BRAINDUMP.md](../BRAINDUMP.md) — The source vision: what Momo is and will become
- [PILLARS.md](../PILLARS.md) — The decision function / operating doctrine (canonical home)

## Existing Documentation

The 2026-07-16 `project-scan-report.json` and `source-tree-analysis.md` describe
the initial pre-runtime scan and are retained as explicitly historical
artifacts. Current runtime truth lives in `skill/`, `tests/`, and the four
current docs linked above. The hand-authored product docs remain `BRAINDUMP.md`
and `PILLARS.md` at the repo root.

## Getting Started

### Prerequisites

`mise`, `op` (1Password CLI), `git`, BMAD v6.10.1 (installed under `_bmad/`), and access to
the `33god` Plane workspace.

### Setup

```bash
cd /home/delorenj/code/33GOD/momo
mise trust && mise install
op inject -i .env.op > .env    # materialize secrets (also runs on `mise enter`)
mise tasks                     # list runnable tasks
```

### Run Locally

```bash
python3 skill/scripts/lifecycle_client.py --help
python3 skill/scripts/obligation_worker.py --help
```

### Run Tests

```bash
mise run lint
mise run test
```

## For AI-Assisted Development

This documentation was generated to let AI agents understand and extend Momo. Because the
the broader promotion remains incomplete, distinguish the implemented client
and durable actor under `skill/` from future agent fanout, heartbeat, and MCP
surfaces.

### When Planning New Features / Starting the Build

- **Understand the product & doctrine:** read [BRAINDUMP.md](../BRAINDUMP.md) +
  [PILLARS.md](../PILLARS.md) first. The Pillars are the source of Momo's
  business choices; the v3 PRD/architecture are authoritative for component boundaries.
- **Understand the intended system:** [architecture.md](./architecture.md) (esp. §4
  components, §5 decision function, §10 the gap).
- **Understand the scaffold & how to work here:** [development-guide.md](./development-guide.md).
- **Avoid the framework noise:** ignore `.claude/`, `.agents/`, `.opencode/`, `.github/`,
  `_bmad/` — these are fanned-out ecosystem config, not Momo's code
  ([why](./source-tree-analysis.md#signal-vs-noise-read-this-first)).
- **Reference implementation:** the working skill at `~/code/33GOD/skills/momo` (lift SSOT),
  **Toad** `src/fanout` (the install/adapter engine to reuse), and the **Hermes template**
  (heartbeat, soul/role modeling, memory wiring — for the deferred autonomous twin).

### Current boundary

The corrected build-planning chain is complete (2026-07-18): see
[product-brief](../_bmad-output/planning-artifacts/product-brief.md),
[PRD](../_bmad-output/planning-artifacts/PRD.md), and
[epics](../_bmad-output/planning-artifacts/epics.md). The conforming Lifecycle
client seam and durable obligation actor are now implemented; future work
starts with packaging/fanout and autonomy only after the shared WIP-lock and
deployment gates are proven.

---

_Documentation generated by BMAD Method `document-project` and reconciled by
Correct Course through the durable actor update on 2026-07-19._
