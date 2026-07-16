# Momo - Architecture

**Date:** 2026-07-16
**Status:** Pre-implementation. This document captures the **intended** architecture
(distilled from [BRAINDUMP.md](../BRAINDUMP.md) + [PILLARS.md](../PILLARS.md) + the 33GOD
ecosystem), the **current reality** (a scaffold), and the **gap** between them.

---

## 1. Executive Summary

Momo is a **provider-agnostic, framework-agnostic agentic PM/EM component**. Its job is to
run a project's ticket board and delegate all implementation to subagents, making
unblocking decisions on the CEO's behalf via a declarative decision function (The Pillars).

The architecture is deliberately **modular and pluggable** so Momo can be *lifted into any
project without surgery* (Pillar #3) and *installed into any agent CLI via adapters*. It
is the **interactive twin** of the autonomous **Hermes PM**; both share one Plane board and
one Hindsight bank per project.

**Today** the repo contains only vision + doctrine + scaffold. **The build** is the
promotion of the proven skill at `~/code/skillex/all-skills/momo` into the six formal
components below.

## 2. Architectural North Star (from BRAINDUMP)

1. **Modular, pluggable, extensible** — never tied to a specific agentic platform or CLI.
2. **Integrates with any CLI via a fan-out set of adapters** — one generic core, many carriers.
3. **PM + EM hybrid** — owns the ticket board *and* delegates tasks to subagents.
4. **Deep domain understanding** — trusted to make unblocking decisions on the CEO's behalf.

## 3. Current Reality vs. Target

| Dimension | Current (2026-07-16) | Target |
|---|---|---|
| Form | pjangler CommonProject scaffold + 2 docs | Formal 33GOD component (6 parts) |
| Product code | **none** | MCP server + agent spec + adapters + heartbeat |
| Working impl | lives at `~/code/skillex/all-skills/momo` (a skill) | promoted & generalized into this repo |
| Ticket board | `.project.json` → Plane `33god/MOMO`, `board_id` empty, `state: planned` | live board driven via `tp`/Trello adapter |
| Runtime driver | none | manual (Telegram/CLI/web/Bloodbank) **or** heartbeat interval |
| Memory | (inherits current Hermes PM bank) | Hindsight, one bank per project |
| Decisions | doctrine written (PILLARS.md) | doctrine *executed* + logged to Bloodbank |

## 4. Component Breakdown

Momo-the-component is six liftable parts. Status reflects this scan.

### 4.1 Skill package  ·  status: 🟡 exists elsewhere, not promoted

The precise workflows that are Momo's job description: survey board → triage/refine →
decide-what's-next → orchestrate a ticket (delegating all code) → review → clear the board
→ record decisions. Proven today as `~/code/skillex/all-skills/momo`; this repo promotes it.
The interactive `momo` skill/agent already published in the ecosystem is the reference shape.

### 4.2 MCP server (provider proxy)  ·  status: 🔴 not started

A **third** MCP server that sits *above* the existing **Plane** server and the existing
**Trello** server as a **proxy** exposing **high-level PM verbs** (e.g. list-board,
triage-ticket, pick-next, move-lane, record-decision). It **delegates** each verb to the
correct backend based on the project's configured provider.

- **Pattern:** **Proxy** (unified PM facade) + **Strategy/Adapter** (per-provider backend)
  + **Factory** (construct the backend from `.project.json`).
- **Resolution:** provider comes from `.project.json.ticket_provider.type`
  (`plane` today; `trello` via bundled adapter + `.momo/config.json` lane map).

### 4.3 Generic agent definition  ·  status: 🔴 not started

A **CLI-agnostic** agent spec (role + personality) kept as generic as possible. Every CLI
has its own format (Claude, OpenCode, Copilot, Kimi, Gemini, …), so the spec itself carries
no CLI specifics — those are applied by adapters. Reference: the **Hermes** model, where
personality is a *soul* file and role is a *role* file; the generic spec is what an adapter
ports *into* that shape.

### 4.4 Agent adapters (fan-out)  ·  status: 🔴 not started

Adapters port the generic core into each target environment. Planned:
**Hermes · Codex · OpenCode · Kimi · Gemini · Claude**.

- **Pattern:** **Adapter** per CLI, driven by the same SSOT fan-out mechanic the repo
  already uses for its BMAD skill trees (`.claude/`, `.opencode/`, `.github/agents/`).
- The **Hermes adapter** is the bridge to the existing fleet: it takes the generic spec and
  emits the soul + role files a Hermes PM expects.

### 4.5 Heartbeat interval service  ·  status: 🔴 not started (reference exists)

Gives Momo **agency**: on each tick it evaluates a declarative goal set against The Pillars
and acts. Today this capability *is* the Hermes fleet's **systemd** interval PMs; the plan
is to **lift that mechanism into this component** largely unchanged.

- **Pattern:** **Observer/scheduler loop** (tick → evaluate → act) over a declarative goal
  set; **Template Method** for the per-tick procedure.

### 4.6 Memory (Hindsight)  ·  status: 🟢 model decided

Hindsight is the memory framework. **One bank per project** — memory is scoped by *project,
not by agent identity* — and Momo keeps **the same bank** the current Hermes PM uses (no
split by identity). The `momo` bank already holds retained doctrine/conventions.

## 5. The Decision Function — The Pillars

Momo decides on the CEO's behalf using [PILLARS.md](../PILLARS.md) (canonical; **reference,
never fork**). Priority order — lower number wins ties:

1. **Chase the Check** — rank by shortest path to a real payment.
2. **Dogfood the Platform** — build products *on* 33GOD; each product hardens a platform
   piece, each platform piece must earn its keep on a revenue product.
3. **Build LEGO, Not Statues** — abstract for reuse; *done = liftable without surgery*.
   Refereed by the **Rule of Three**: abstract on the **second** occurrence, not the first.
4. **Gang of Four by Default** — name the standard pattern first; descend to domain
   patterns (outbox, saga, CQRS) only when genuinely event-driven.

**On a tick**, Momo walks candidates through #1 → #2 → (#3 + Rule of Three) → #4, and when
forced to decide while blocked, the lowest-numbered applicable pillar is the tiebreaker.

> **Momo is the Rule of Three made flesh:** it shipped concrete as a skill, got proven, and
> is *now* (second occurrence) being extracted into a reusable component — earned, not guessed.

## 6. Design Patterns (Pillar #4 mapping)

Naming the GoF pattern is doctrine, so the intended design is stated in those terms:

| Concern | Pattern(s) |
|---|---|
| Unified PM API over Plane/Trello servers | **Proxy** + **Facade** |
| Selecting the ticket backend at runtime | **Strategy** + **Factory** (from `.project.json`) |
| Installing into each agent CLI | **Adapter** (fan-out) |
| Provider lane/status mapping (Trello) | **Adapter** + config map (`.momo/config.json`) |
| Per-tick autonomous procedure | **Template Method** + scheduler/**Observer** loop |
| Composing workflow steps (triage→refine→orchestrate) | **Composite** / **Chain of Responsibility** |
| Emitting decision provenance | **Observer** (publish to Bloodbank) |

## 7. Cross-Cutting Concerns

### Events — Bloodbank

Momo records consequential judgment calls as **Bloodbank** decision events, tagged against
the pillars. Bloodbank is the 33GOD event bus (NATS/dapr). This makes Momo's decisions
auditable and lets other components (Candystore persistence, Holocene control plane) react.

### Provider agnosticism

`.project.json` is the resolution root: `ticket_provider.type` picks Plane (via the repo
`tp` adapter) or Trello (bundled adapter). Momo never hard-codes a provider.

### Secrets & config

Secrets flow through **1Password** (`op inject -i .env.op > .env` on `mise enter`). Nothing
sensitive is committed (`.env` is gitignored; `.env.op` holds only references).

## 8. Relationship to Hermes (the autonomous twin)

Momo and the **Hermes PM** are two drivers of the *same* system:

- **Same** Plane board, **same** Hindsight bank per project.
- **Hermes** = autonomous, systemd-heartbeat PM provisioned per project by the fleet.
- **Momo** = the human-drivable, interactive counterpart of that same role.
- The end state: a **Hermes adapter** lets the generic Momo core *become* a Hermes PM (soul
  + role), so today's fleet behavior is just "Momo installed via the Hermes adapter."

Implementers should **read the Hermes fleet implementation** as the primary reference for
the heartbeat, role/soul modeling, and memory wiring.

## 9. Placement in the 33GOD Ecosystem

```
Bloodbank (NATS/dapr event bus)  ←── Momo emits decision events
Candystore (event persistence)   ←── consumes/audits
Holocene  (control plane + dash)  ←── observes/controls
pjangler  (project registry/bootstrap) ── scaffolded this repo (.project.json)
Hermes-fleet (autonomous PM twin) ── shares board + bank; Hermes adapter target
Plane / Trello (ticket backends)  ←── proxied by Momo's MCP server
Hindsight (memory framework)      ←── one bank per project
```

## 10. The Gap — what "build Momo" entails

To go from scaffold → working component:

1. **Choose the implementation language/runtime** for the MCP server + adapters (undecided).
2. **Promote the skill** (`~/code/skillex/all-skills/momo`) into this repo and generalize it.
3. **Build the provider-proxy MCP server** (Proxy + Strategy/Factory over Plane & Trello).
4. **Extract the generic agent spec** and build the **six adapters** (Hermes first).
5. **Lift the heartbeat** from the Hermes fleet into a Momo-owned interval service.
6. **Wire Bloodbank** decision-event publishing and **Hindsight** per-project memory.
7. **Close the scaffold gaps** (see development-guide) so `mise enter` is clean.

## 11. Testing Strategy (intended)

- No tests exist yet (no code). When implemented: contract-test the MCP proxy against
  Plane/Trello backends, golden-test each adapter's rendered output against its CLI's
  expected format, and simulate heartbeat ticks against fixture boards to validate the
  pillar-ranking decision function.

## 12. Deployment (intended)

- **Manual gateways:** Telegram, CLI, web, Bloodbank message.
- **Autonomous:** a **systemd** user interval unit (mirroring the Hermes fleet) driving the
  heartbeat on a declarative goal set. Provisioning lifted from the fleet into this component.

---

_Generated using BMAD Method `document-project` workflow. Content reflects intended design
from source docs; it is not reverse-engineered from code (none exists yet)._
