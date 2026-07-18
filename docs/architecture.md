# Momo - Architecture

**Date:** 2026-07-18
**Status:** Pre-implementation (promotion job). This document captures the **intended**
architecture (distilled from [BRAINDUMP.md](../BRAINDUMP.md) + [PILLARS.md](../PILLARS.md) +
the 33GOD ecosystem), the **current reality**, and the **gap**.

> **Reality update (2026-07-16, post-research):** A 4-investigator grounding pass corrected
> three earlier assumptions in this doc. (1) The working Momo is a **fully functional skill**
> at **`~/code/33GOD/skills/momo`** (not the stale `skillex` path BRAINDUMP cites) — this is a
> **promotion**, not a greenfield build. (2) The **MCP proxy server is DEFERRED** (Rule of
> Three), not a core MVP part — `momo-board.sh` already is the working proxy. (3) The
> implementation **language is decided** (two-tier: Python/Bash glue + TS/Node wrapper). The
> forward plan now lives in the planning artifacts:
> [product-brief](../_bmad-output/planning-artifacts/product-brief.md) ·
> [PRD](../_bmad-output/planning-artifacts/PRD.md) ·
> [epics](../_bmad-output/planning-artifacts/epics.md). Sections below are annotated where superseded.

> **Approved boundary correction (2026-07-18):** Momo is an intelligent PM/EM
> process-manager, not the lifecycle state machine. The separate headless
> Lifecycle component owns versioned spec/state, deterministic reconciliation,
> legal frontier, obligations, and capability validation. The service is not
> implemented; the tested Bloodbank lifecycle controller is its extraction
> embryo. Direct `tp`/Trello transitions described as current behavior below are
> legacy migration paths, not the target contract.

---

## 1. Executive Summary

Momo is a **provider-agnostic, framework-agnostic agentic PM/EM component**. Its
job is to understand the business, select among actions authorized by Lifecycle,
delegate all implementation, independently review evidence, and submit auditable
intent on the CEO's behalf using The Pillars. It never calculates or writes
lifecycle truth.

The architecture is deliberately **modular and pluggable** so Momo can be *lifted into any
project without surgery* (Pillar #3) and *installed into any agent CLI via adapters*. It
is the **interactive twin** of the autonomous **Hermes PM**; both share one Plane board and
one Hindsight bank per project.

**Today** the *repo* contains only vision + doctrine + scaffold — but the *skill* at
`~/code/33GOD/skills/momo` is a fully working PM/EM orchestrator. **The build** is the
**promotion** of that proven skill into a liftable, versioned component (the parts below),
maximizing reuse rather than rebuilding.

## 2. Architectural North Star (from BRAINDUMP)

1. **Modular, pluggable, extensible** — never tied to a specific agentic platform or CLI.
2. **Integrates with any CLI via a fan-out set of adapters** — one generic core, many carriers.
3. **PM + EM hybrid** — owns process policy, prioritization, delegation, and
   review; Lifecycle owns the state machine and provider projections.
4. **Deep domain understanding** — trusted to make unblocking decisions on the CEO's behalf.

## 3. Current Reality vs. Target

| Dimension | Current (2026-07-18) | Target |
|---|---|---|
| Form | pjangler CommonProject scaffold + 2 docs | Formal 33GOD component |
| Product code | **none** | **MVP target:** corrected Lifecycle-client skill SSOT + minimal `momo install`. **Deferred/gated:** generic spec + fanout (E4), heartbeat (E5), MCP proxy (E6) |
| Working impl | fully-working skill at `~/code/33GOD/skills/momo` | promoted & generalized into this repo |
| Ticket/lifecycle | `.project.json` → provider board; current skill can write direct transitions | authoritative Lifecycle snapshot/frontier; provider board is a projection and Momo submits intent only |
| Runtime driver | none in this repo | manual or heartbeat Lifecycle client; no local reconciler |
| Memory | (inherits current Hermes PM bank) | Hindsight, one bank per project |
| Decisions | doctrine written (PILLARS.md) | doctrine *executed* + logged to Bloodbank |

## 4. Component Breakdown

Momo-the-component is six liftable parts. Status reflects this scan.

### 4.1 Skill package  ·  status: 🟢 WORKING at `33GOD/skills/momo` — lift into repo

The precise workflows that are Momo's job description: inspect authoritative
work → apply business policy → orchestrate a ticket (delegating all code) →
review → submit intent/evidence → record decisions. The policy/delegation loop is
implemented and proven today at `~/code/33GOD/skills/momo`
(SKILL.md + 6 references + 3 templates + `scripts/{momo-board.sh, record-decision.py,
momo-config.py, providers/trello.py}`). The promotion preserves this behavior but
must replace direct provider transitions with the Lifecycle client seam; the
current scripts are not target-contract complete.

### 4.2 MCP server (provider proxy)  ·  status: ⛔ DEFERRED (Rule of Three — 2nd consumer)

> **Corrected (D5):** `momo-board.sh` is the current provider adapter. Its reads
> can support a projection during migration, but its transition operation is a
> legacy direct writer. The target MCP/client reads Lifecycle snapshots and
> submits versioned, idempotent intent through Bloodbank.

When a second consumer needs programmatic access, build a thin TS MCP with
coarse snapshot/frontier, observation/evidence, decision-provenance, and intent
verbs. Every state-changing verb delegates to Lifecycle; provider adapters are
read projections/migration aids only.

- **Pattern:** **Proxy/Facade** (small coarse PM API) + **Strategy** (per-provider backend)
  + **Factory** (backend from `.project.json`). Language: **TypeScript** (toad/pjangler norm).

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

### 4.5 Heartbeat interval service  ·  status: ⛔ DEFERRED/GATED (E5; reference exists)

Gives Momo **agency**: on each tick it evaluates a declarative goal set against The Pillars
and acts. Today this capability *is* the Hermes fleet's **systemd** interval PM — specifically
the **scrum-master** role's `continuous-ticket-sentinel` (a `.timer` firing a cheap bash gate
around one LLM pass). ⚠️ **Not** the gateway `pm` role, which is event-driven (Telegram +
bloodbank inbox) — the two are provisioned differently, and E5 must target the sentinel path.
The plan reuses the sentinel trigger/provisioning mechanism. Its policy pass must
be corrected to the same Lifecycle client protocol as interactive Momo; no
sentinel reconciliation/state writer is lifted into Momo.

- **Pattern:** **Scheduler** / polling loop (timer → gate → pass); **Template Method** for the
  per-tick procedure. *(Not Observer — a fixed-interval poll has no state-change subscription.)*

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

### 5a. Two-tier decision function (don't conflate)

The 4 pillars above are the **product** tier (`PILLARS.md`, per-repo `.momo/pillars.md`). The
as-built skill *also* carries a **process** tier in `references/pillars.md` — universal
operating slugs Momo cites as decision `basis[]`: `keep-the-pipeline-unblocked`,
`delegate-every-code-change`, `evidence-over-status`, `independent-adversarial-review`,
`everything-is-an-event`, `bias-to-reversible-action`, `respect-the-contracts`,
`one-source-of-truth`, `smallest-safe-increment`. (E.g. the `board_id` self-heal records
basis = `one-source-of-truth` + `respect-the-contracts` — process slugs, not product ones.)

**Safety-supremacy invariant:** the process/safety pillars (no-code-mutation,
reviewer-independence, evidence, respect-the-contracts) are **never** overridden by a product
pillar — Chase-the-Check can reorder *what* Momo does, never *whether* it delegates code or
reviews independently. Any `basis[]` validator must accept **both** tiers.

## 6. Design Patterns (Pillar #4 mapping)

Naming the GoF pattern is doctrine, so the intended design is stated in those terms:

| Concern | Pattern(s) | On critical path? |
|---|---|---|
| Unified PM API over Lifecycle snapshots and commands | **Proxy** + **Facade** | ⛔ deferred (E6) |
| Selecting a provider projection at runtime | **Strategy** + **Factory** (from `.project.json`) | ✅ migration support |
| Installing into each agent CLI | **Adapter** (fan-out) | ▫ E4 (2nd occurrence) |
| Provider lane/status projection (Trello) | **Adapter** + config map (`.momo/config.json`) | ✅ legacy/read support |
| Per-tick procedure | **Template Method** (fixed skeleton, overridable steps) | ⛔ deferred (E5) |
| Heartbeat trigger | **Scheduler** / polling loop *(not Observer — no subscription)* | ⛔ deferred (E5) |
| Composing workflow steps (triage→refine→orchestrate→review) | **Pipeline** (fixed-order stages) *(not Composite/Chain of Responsibility)* | ✅ MVP (proven) |
| Emitting decision provenance | **Observer** (genuine publish/subscribe to Bloodbank) | ✅ MVP (wired) |

## 7. Cross-Cutting Concerns

### Lifecycle authority

Lifecycle is the single deterministic writer. A Momo pass starts with an
authoritative snapshot containing lifecycle/project identity, spec/state
versions, legal frontier, obligations, blockers, and capability grants. Momo
applies product/process pillars only to rank legal candidates, then submits an
idempotent command with expected state version. Accepted, rejected, stale, and
unavailable results are rendered without optimistic local state.

Momo may emit observations, evidence, and review verdicts. Its
`repo.decision.recorded` event explains *why* it chose an action; it never makes
that action legal or mutates state.

### Events — Bloodbank

Momo records consequential judgment calls as Bloodbank decision events tagged
against the pillars. Bloodbank owns canonical schemas and NATS/Dapr transport;
Candystore persists history/read models. Neither event publication nor durable
history transfers Lifecycle's state authority to Momo.

### Provider agnosticism

`.project.json` supplies PJangler-owned project/bootstrap identity and selects a
provider projection. It does not contain authoritative lifecycle state. Momo
never hard-codes a provider or derives legal state from a lane.

### Secrets & config

Secrets flow through **1Password** (`op inject -i .env.op > .env` on `mise enter`). Nothing
sensitive is committed (`.env` is gitignored; `.env.op` holds only references).

## 8. Relationship to Hermes (the autonomous twin)

Momo and the **Hermes PM** are two clients of the same Lifecycle authority:

- **Same** Lifecycle snapshot/command contract, provider projection, and
  Hindsight bank per project — so they must not double-dispatch.
  WIP=1 needs a **real shared lock** (not politeness): the Hermes sentinel fires on a ~60s
  timer, so an advisory "read state, then act" has a TOCTOU race. This coexistence lock is on
  the **MVP** critical path (E2/S2.3) the instant Momo installs onto a Hermes-run repo — it is
  *not* deferred with E5.
- **Hermes** runs two distinct models: the **gateway `pm`** role (event-driven: Telegram +
  bloodbank inbox) and the **scrum-master** role (the systemd **interval** `continuous-ticket-sentinel`).
  The interval heartbeat is the scrum-master, not the pm.
- **Momo** = the human-drivable, interactive policy client. The deterministic
  reconcile loop lives in Lifecycle, not either PM client.
- The end state: a **Hermes adapter** (net-new provisioning bridge — renders soul+role **and**
  shells out to the copier template; *not* a file-render) lets the generic Momo core *become* a
  Hermes PM. It must **neutralize honcho** (Hermes' native per-agent memory) so the twin uses
  only the shared Hindsight bank.

Implementers should **read the Hermes fleet implementation** as the primary reference for
the heartbeat, role/soul modeling, and memory wiring.

## 9. Placement in the 33GOD Ecosystem

```
PJangler (project/bootstrap identity) ──> Lifecycle binding
Bloodbank (schemas + transport) <──────> Lifecycle commands/events
Lifecycle (spec/state/reconcile/frontier/obligations/capabilities)
        ├──> Candystore (durable history/read models)
        ├──> Momo/Hermes (policy clients: select, delegate, review, intent)
        ├──> Holocene (renderer/high-level command client)
        └──> Plane/Trello (provider projections via adapters)
Hindsight (memory) <──────────────────── Momo/Hermes shared project bank
Toad (project custodian) ─────────────── births/audits; fanout reuse
```

## 10. The Gap — what "build Momo" entails (corrected & sequenced)

Language is **decided** (two-tier: preserved Python/Bash policy glue + TS/Node
wrapper à la toad/pjangler). Decision events + memory are already wired in the
skill; direct state writes are intentionally replaced. The real work
is packaging & seams, sequenced by shortest-path-to-demo — full backlog in
[epics.md](../_bmad-output/planning-artifacts/epics.md):

1. **External dependency — Lifecycle:** extract the Bloodbank controller embryo
   with history, close schemas/outbox, add spec/frontier/obligation/capability and
   command seams, and pass migration/replay/rollback gates.
2. **E0 — Client prerequisite:** resolve PJangler identity, Lifecycle
   snapshot/commands/grant, and provider projection; repair bindings as metadata.
3. **E1 — Promote the policy skill:** preserve pillars, delegation, review, and
   decision provenance while removing direct state authority.
4. **E2 — Install + target demo:** gate doctor on Lifecycle, submit versioned
   intent/evidence, and prove no direct provider transition.
5. **E3–E4:** package and fan out the corrected client contract.
6. **E5:** Hermes adapter remains a policy client, never another reconciler.
7. **E6:** thin MCP over Lifecycle reads/commands, not provider transition APIs.

## 11. Testing Strategy (intended)

- No product tests exist yet. When implemented: contract-test the Momo client
  against Lifecycle snapshot/command versions; prove stale-version, denied-grant,
  duplicate-command, and unavailable-service behavior; golden-test provider read
  projections; and verify Pillars only rank actions in the legal frontier.

## 12. Deployment (intended)

- **Manual gateways:** Telegram, CLI, web, or Bloodbank message feed the Momo
  client; Lifecycle remains the state writer.
- **Autonomous:** a **systemd** user interval unit (mirroring the Hermes fleet) driving the
  policy pass on a declarative goal set. Provisioning is lifted from the fleet;
  reconciliation is not.

---

_Generated using BMAD Method `document-project` workflow and reconciled through
Correct Course on 2026-07-18. Momo product code and the standalone Lifecycle
vertical slice are not implemented._
