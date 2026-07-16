# Momo Documentation Index

**Type:** Monolith (pjangler CommonProject) — agentic PM/EM component
**Primary Language (decided):** Python3-stdlib + Bash (skill glue, lifted verbatim) · TypeScript/Node (component wrapper, toad norm)
**Architecture:** Modular, adapter-based, provider-agnostic
**Status:** Pre-implementation — **promotion job** (working skill exists; repo is being packaged)
**Last Updated:** 2026-07-16
**Forward plan:** [product-brief](../_bmad-output/planning-artifacts/product-brief.md) · [PRD](../_bmad-output/planning-artifacts/PRD.md) · [epics](../_bmad-output/planning-artifacts/epics.md)

## Project Overview

**Momo** is 33GOD's *Agentic Ticketing Workflow and Project Lifecycle System* — a
project-manager + engineering-manager hybrid agent that owns a project's ticket board,
delegates all code changes to subagents, and makes unblocking decisions on the CEO's behalf
via a declarative decision function ([The Pillars](../PILLARS.md)). It is the interactive
twin of the autonomous **Hermes PM** and shares its Plane board and Hindsight bank per
project.

This repo is the **promotion target**: the **fully-working skill** at `~/code/33GOD/skills/momo`
is being formalized into a reusable, versioned component (packaged skill + generic agent spec
+ fanout adapters; MCP proxy and heartbeat **deferred**). **No product code exists in this
repo yet** — the working behavior lives in the skill and gets lifted here.

## Quick Reference

- **Repository Type:** Monolith (single `pjangler` CommonProject repo)
- **Entry Point:** `mise.toml` (operational); no product entry point yet
- **Architecture Pattern:** Proxy (over Plane/Trello) + Adapter (per CLI) + Strategy/Factory + heartbeat loop
- **Ticket Board:** Plane, workspace `33god`, identifier `MOMO` (`state: planned`)
- **Memory:** Hindsight, one bank per project (`momo` bank)
- **Events:** Bloodbank (NATS/dapr) — decision provenance tagged against The Pillars
- **Secrets:** 1Password via `op inject -i .env.op > .env`
- **Versioning:** git tags (mise-versioning)

## Generated Documentation

### Core Documentation

- [Project Overview](./project-overview.md) — Executive summary and high-level architecture
- [Source Tree Analysis](./source-tree-analysis.md) — Annotated directory structure (signal vs. framework noise)
- [Architecture](./architecture.md) — Intended architecture, current reality, the gap, and GoF pattern mapping
- [Development Guide](./development-guide.md) — Tooling, secrets, versioning, planning workflow, and known scaffold gaps

### Not Yet Applicable (no implementation)

The following are standard for a code project but **do not apply yet** — there is no source
code, API, data layer, or UI. They will be generated when implementation begins:

- Component Inventory — *(planned components are catalogued in [architecture.md §4](./architecture.md#4-component-breakdown))*
- API Contracts — *(the intended MCP tool surface is described in [architecture.md §4.2](./architecture.md#42-mcp-server-provider-proxy)) — To be generated when the MCP server is built*
- Data Models — *(no data layer; state lives in Plane/Trello + Hindsight + Bloodbank events)*
- Deployment Guide — *(intended heartbeat/systemd deployment sketched in [architecture.md §12](./architecture.md#12-deployment-intended)) — To be generated when the service exists*

## Source Documents (product signal)

- [BRAINDUMP.md](../BRAINDUMP.md) — The source vision: what Momo is and will become
- [PILLARS.md](../PILLARS.md) — The decision function / operating doctrine (canonical home)

## Existing Documentation

Before this scan, the project had no `docs/` content. The hand-authored product docs are
`BRAINDUMP.md` and `PILLARS.md` at the repo root (linked above).

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
# No product code yet — nothing to run.
# Planning is done via BMAD skills, e.g.:
#   /bmad-bmm-document-project   (produced this docs/ set)
```

### Run Tests

```bash
# No tests yet — no code exists.
```

## For AI-Assisted Development

This documentation was generated to let AI agents understand and extend Momo. Because the
project is pre-implementation, treat these docs as the **design brief**, not a codebase map.

### When Planning New Features / Starting the Build

- **Understand the product & doctrine:** read [BRAINDUMP.md](../BRAINDUMP.md) +
  [PILLARS.md](../PILLARS.md) first — they are the source of truth.
- **Understand the intended system:** [architecture.md](./architecture.md) (esp. §4
  components, §5 decision function, §10 the gap).
- **Understand the scaffold & how to work here:** [development-guide.md](./development-guide.md).
- **Avoid the framework noise:** ignore `.claude/`, `.agents/`, `.opencode/`, `.github/`,
  `_bmad/` — these are fanned-out ecosystem config, not Momo's code
  ([why](./source-tree-analysis.md#signal-vs-noise-read-this-first)).
- **Reference implementation:** the working skill at `~/code/33GOD/skills/momo` (lift SSOT),
  **Toad** `src/fanout` (the install/adapter engine to reuse), and the **Hermes template**
  (heartbeat, soul/role modeling, memory wiring — for the deferred autonomous twin).

### Next Logical Step

The build-planning chain is **done** (2026-07-16): see
[product-brief](../_bmad-output/planning-artifacts/product-brief.md),
[PRD](../_bmad-output/planning-artifacts/PRD.md), and
[epics](../_bmad-output/planning-artifacts/epics.md). Next: bring up the MOMO board (**E0**)
and start **E1 — promote the skill** into this repo.

---

_Documentation generated by BMAD Method `document-project` workflow_
