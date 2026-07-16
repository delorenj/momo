# Momo - Project Overview

**Date:** 2026-07-16
**Type:** Agentic PM/EM component (pre-implementation) within the 33GOD platform
**Architecture:** Modular, adapter-based, provider-agnostic (intended)

## Executive Summary

**Momo** is 33GOD's *Agentic Ticketing Workflow and Project Lifecycle System* — an
AI "employee" that plays a **project-manager + engineering-manager hybrid**: it owns a
project's ticket board, refines and prioritizes work, delegates every code change to
subagents (it never edits code itself), reviews to a high bar, and is entrusted to make
unblocking decisions **on the CEO's behalf** using a declarative decision function (see
[PILLARS.md](../PILLARS.md)).

This repository is **not yet an implementation** — it is the **promotion target** for an
existing, proven skill. Momo currently lives as a single working skill at
`~/code/skillex/all-skills/momo`; this repo is where that skill is being promoted into a
formal, reusable 33GOD **component** (skill package + MCP server + generic agent
definition + adapters + heartbeat service + memory). As of this scan, the repo contains
the **vision** ([BRAINDUMP.md](../BRAINDUMP.md)), the **doctrine** ([PILLARS.md](../PILLARS.md)),
and a **pjangler CommonProject scaffold** — no product source code has been written here yet.

> Momo is the **interactive / human-drivable twin** of the **autonomous Hermes PM**. Both
> share the same Plane board and the same per-project Hindsight memory bank. The end state:
> what Hermes does autonomously on a heartbeat, Momo can also do manually — and be installed
> into *any* agent CLI (Claude, Gemini, Codex, OpenCode, Kimi) via fan-out adapters.

## Project Classification

- **Repository Type:** Monolith (single `pjangler` CommonProject repo)
- **Project Type(s):** Agentic component / platform building block — pre-implementation.
  Target surface spans a **backend service (MCP server)**, a **CLI/skill workflow**, and
  an **agent definition + adapters**. Does not map cleanly onto a single BMAD project type
  (web/backend/cli/library/…); it is a *composite* component.
- **Primary Language(s):** None committed yet. Scaffold is Markdown + TOML + Bash. The
  implementation language for the MCP server and adapters is **undecided** (TypeScript or
  Python are the 33GOD norms; to be chosen during planning).
- **Architecture Pattern:** *Intended* — Proxy over ticket providers, Adapter for agent
  CLIs, Strategy for provider selection, plus an event-driven heartbeat loop. See
  [architecture.md](./architecture.md).

## What Momo Is (four facets)

From [BRAINDUMP.md](../BRAINDUMP.md), Momo is simultaneously:

1. **An agent specification** — a role + personality, kept deliberately CLI-agnostic.
2. **A skill package** — the precise workflows that constitute its job (triage, refine,
   decide-what's-next, orchestrate a ticket, review, clear the board, record decisions).
3. **An MCP server** — high-level PM tools that proxy down to a Plane server and a Trello
   server, selecting the backend based on the project's configured ticket provider.
4. **A framework-agnostic package with adapters** — installable into any agent CLI, plus a
   heartbeat interval service that gives it autonomous agency on a declarative goal set.

## Key Features (target capabilities)

- **Board ownership** — survey, triage, refine, and prioritize tickets on a Plane or
  Trello board via a provider-agnostic adapter (`tp`).
- **Delegation, not authorship** — orchestrates implementation by dispatching every code
  change to subagents; Momo itself stays out of the editor.
- **Decision function** — ranks candidate actions by walking [The Pillars](../PILLARS.md)
  in priority order; when blocked, the lowest-numbered applicable pillar is the tiebreaker.
- **Decision provenance** — records consequential judgment calls as **Bloodbank** decision
  events tagged against the pillars.
- **Provider agnosticism** — Plane/Linear (via the repo `tp` adapter) or Trello (bundled
  adapter + `.momo/config.json` lane map), resolved from `.project.json`.
- **Per-project memory** — Hindsight, one bank per project (kept identical to the current
  Hermes PM bank; memory is scoped by *project*, not by agent identity).

## Architecture Highlights

- **Provider proxy MCP** sits *above* the existing Plane MCP and the existing Trello MCP,
  exposing coarse PM verbs and delegating to whichever backend the project declares.
- **Generic agent spec → per-CLI adapters** (Hermes, Codex, OpenCode, Kimi, Gemini,
  Claude). The Hermes fleet is the reference: personality via a *soul* file, role via a
  *role* file — the generic spec is what an adapter ports *into* those.
- **Heartbeat** mirrors the Hermes fleet's systemd interval PMs — lifted into this
  component rather than reinvented.
- **Dogfooding** — Momo is itself a 33GOD component managed by 33GOD conventions
  (pjangler scaffold, Bloodbank events, Hindsight memory), embodying Pillar #2.

## Development Overview

### Prerequisites

- [`mise`](https://mise.jdx.dev) — task runner, env, and tool management (drives everything).
- [`1Password CLI`](https://developer.1password.com/docs/cli/) (`op`) — secrets are
  materialized by `op inject -i .env.op > .env` on `mise enter`.
- BMAD Method v6.10.1 (installed under `_bmad/`) — planning/documentation workflows.
- Access to the **33god** Plane workspace (project identifier `MOMO`).

### Getting Started

```bash
cd /home/delorenj/code/33GOD/momo
mise trust && mise install      # trust config, install tools
# `mise enter` runs the enter hooks: link agent files, op-inject secrets, (codegraph)
mise run hindsight-setup        # provision the shared project Hindsight key (see note)
mise tasks                      # list available tasks
```

> ⚠️ Two `mise` references currently point at scripts that are not present in the repo
> (`.mise/scripts/codegraph.sh`, `.mise/scripts/hindsight-setup.sh`), and `AGENTS.md` does
> not exist yet, so the agent-file symlink hook no-ops. See
> [development-guide.md](./development-guide.md#known-scaffold-gaps).

### Key Commands

- **Install:** `mise install`
- **Dev:** *(no product code yet — nothing to run)*
- **Build:** *(none yet)*
- **Version:** `mise run version` · `mise run version:bump[-minor|-major]` · `mise run version:check`
- **Test:** *(none yet)*

## Repository Structure

A single `pjangler` CommonProject repo. The **signal** is a small set of hand-authored
docs + scaffold config; the bulk of the file count (~850 files) is **framework
scaffolding** fanned out from the 33GOD ecosystem (BMAD skills, per-CLI agent configs) and
is *not* Momo's own code. See [source-tree-analysis.md](./source-tree-analysis.md) for the
full annotated tree and the signal-vs-noise breakdown.

## Documentation Map

For detailed information, see:

- [index.md](./index.md) — Master documentation index
- [architecture.md](./architecture.md) — Intended architecture, current reality, and the gap
- [source-tree-analysis.md](./source-tree-analysis.md) — Annotated directory structure
- [development-guide.md](./development-guide.md) — Tooling, secrets, versioning, workflow
- [../BRAINDUMP.md](../BRAINDUMP.md) — Source vision (product definition)
- [../PILLARS.md](../PILLARS.md) — The decision function (operating doctrine)

---

_Generated using BMAD Method `document-project` workflow_
