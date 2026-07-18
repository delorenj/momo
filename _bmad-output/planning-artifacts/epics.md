# Momo — Epics & Stories (v3, lifecycle-boundary corrected)

**Date:** 2026-07-18
**Author:** Momo (acting PM, on Jarad's behalf)
**Companion docs:** [product-brief.md](./product-brief.md) · [PRD.md](./PRD.md) · [../../docs/architecture.md](../../docs/architecture.md)
**Revision:** v3 preserves the v2 scope reduction and applies the user-approved
Major Correct Course boundary. Momo is a PM/EM policy client; the separate
Lifecycle component is the deterministic state authority. The root has no epic
set, so these Momo epics are the affected implementation backlog.

**Sequencing principle:** shortest path to a demoable slice on a revenue product,
within actions authorized by Lifecycle. **Target MVP = Revenue Gate + Lifecycle
Gate + E0 + E1 + E2.** Packaging may proceed independently, but lifecycle claims
cannot pass before the gate.

**ACs** are enumerated + testable (they must pass Momo's own triage rubric — dogfooding the gate). **Sizing:** S ≤½d · M ½–1d · L 1–2d (solo).

---

## ⛳ Revenue Gate (answer before E1) — Pillar #2

> **Which revenue-bearing product does Momo dogfood first?** The MVP demo (E2) must run on
> **that product's board**, not on MOMO's own board. Rationale (verified by the review):
> the whole MVP scoped to MOMO-on-MOMO is a *statue* by Pillar #2's own definition ("a
> platform piece with no product pulling on it"), and clearing MOMO's own backlog advances
> no product toward a check (Pillar #1).
>
> **If no revenue product is ready to pull on Momo, the correct pillar-consistent call is to
> DEFER the promotion** and keep using the skill as-is (Rule of Three: don't build the
> abstraction on spec). This is the one input only the CEO can supply.

---

## Epic 0 — Prerequisites & board-drivability  ·  MVP  ·  Pillar #2 enabler

**Lifecycle Gate:** the standalone service has been extracted from the tested
Bloodbank embryo with history preservation; lifecycle command/event schemas and
outbox publication are valid; snapshot/frontier/obligation/capability contracts
exist; and migration/replay/rollback gates pass. This is not true today.

**Goal:** Make a target repo drivable by resolving PJangler identity, an
authoritative Lifecycle client, and a provider projection. The existing
`momo-board.sh` exit-2 behavior remains useful current evidence but does not
replace the Lifecycle gate.

### S0.0 — Implement the Lifecycle client seam  (L) — FR-0
- **AC1** Fetch a snapshot keyed by PJangler project identity with lifecycle ID,
  spec/state versions, legal frontier, obligations, blockers, and grants.
- **AC2** Submit idempotent intent/observation/evidence commands through
  registered Bloodbank contracts with expected state version and capability.
- **AC3** Render accepted, rejected, stale, and unavailable outcomes without a
  direct provider transition or optimistic local write.
- **AC4** A conformance test fails if Momo calculates a transition, obligation,
  frontier, or capability decision locally.

### S0.1 — Provision the provider projection adapter  (M) — FR-5.0
- **AC1** For a **plane/linear** target, a `tp` adapter exists at `<role_dir>/.scripts/lib/ticket-provider.sh` and `.project.json.agents{}` names its `role_dir` — provisioned via a Hermes PM deploy **or** a standalone pjangler `tp` install (a Toad/pjangler action, per boundary D6 — **not** Momo minting it).
- **AC2** `momo-board.sh resolve` returns provider projection identity for the
  target; no result is treated as authoritative Lifecycle state.
- **AC3** For a **trello** target, the bundled adapter needs no `role_dir`, but it
  remains a projection/migration adapter and cannot bypass S0.0.

### S0.2 — `board_id` self-heal  (M) — FR-5.1
- **AC1** When `.project.json.ticket_provider.board_id` is empty, resolve by
  exact board name, backfill the PJangler/bootstrap binding, and submit the
  repaired identity as an observation; do not mutate Lifecycle state.
- **AC2** The backfill is recorded via `record-decision.py` with `data.basis` = process-pillar slug(s) (e.g. `one-source-of-truth`, `respect-the-contracts`).
- **AC3** Zero/multiple matches → **fail loud**, surface candidates, no guess.

> **Demoted to housekeeping (non-blocking):** seeding MOMO's *own* backlog onto its board. It's orthogonal to the E2 demo (which installs into a *different* repo) — do it opportunistically, off the critical path.

---

## Epic 1 — Promote the skill (SSOT), correctly  ·  MVP  ·  Pillar #3

**Goal:** The proven PM/EM policy becomes the repo's SSOT. Preserve delegation,
review, pillars, and provenance while replacing legacy transitions with the
Lifecycle client and parameterizing actor identity.

### S1.1 — SSOT-drift resolution + no-fork guarantee  (M) — FR-1.1
- **AC1** Confirm `33GOD/skills/momo` is canonical (the `skillex` path is dead); record the decision.
- **AC2** After the lift, the operator's **global** installed skill is regenerated-from / symlinked-to the repo master (no second drifting copy); `momo fanout check` (E4) is scoped to cover the global install.
- **AC3** BRAINDUMP/doc references to the stale path are corrected.

### S1.2 — Promote proven policy and isolate required changes  (M) — FR-0, FR-1, FR-6
- **AC1** `SKILL.md`, `references/*`, `templates/*`, and current scripts are in
  the repo; policy/delegation/review/provenance behavior is spot-verified while
  target transition behavior conforms to S0.0 rather than direct provider writes.
- **AC2** `record-decision.py` `actor.cli`/`actor.provider` are parameterized
  from the active carrier. Preserve the event type, derived subject, and
  dual-sink, not the hardcoded actor identity.
- **AC3** Scripts stay stdlib-only (python3 + bash); no new deps.

### S1.3 — Two-tier pillar fidelity  (S) — FR-6.2
- **AC1** The lift preserves **both** tiers: universal **process** pillars (`references/pillars.md`: `keep-the-pipeline-unblocked`, `delegate-every-code-change`, `evidence-over-status`, `independent-adversarial-review`, `everything-is-an-event`, `bias-to-reversible-action`, `respect-the-contracts`, `one-source-of-truth`, `smallest-safe-increment`) **and** the 4 **product** pillars (`PILLARS.md`).
- **AC2** Any decision-basis validation/test accepts **process-pillar** slugs (the board_id self-heal uses them) — not only the 4 product slugs.
- **AC3** The **safety-supremacy invariant** is documented: safety/process pillars (no-code-mutation, reviewer-independence, evidence, respect-the-contracts) are never overridden by a product pillar.

### S1.4 — Prove one authority with Hermes  (M) — NFR-1
- **AC1** Run the same provider projection through Momo and Hermes; assert
  normalized read output is identical, then prove both clients use the same
  Lifecycle snapshot/command contracts for state-changing intent.
- **AC2** Assert `momo-board.sh` resolves the **same** `role_dir`/`tp` instance Hermes binds to (no divergent copy).
- **AC3 (Trello)** Golden differential test: Momo's `trello.py` and Hermes'
  adapter return identical read projections on a fixture. Neither adapter is
  permitted to author target lifecycle truth.

### S1.5 — Reconcile the process-manager pass definition  (M) — NFR-1
- **AC1** The lifted Momo loop and Hermes pass share one client protocol: fetch
  authoritative snapshot, select from legal frontier, submit intent/evidence,
  and render the resulting state.
- **AC2** On a repo with both clients, command idempotency and expected-version
  rejection prevent duplicate/conflicting state writes; WIP=1 also prevents
  duplicate worker dispatch.
- **AC3** Divergence between the two is caught by a check (they can't silently drift).

### S1.6 — Doc corrections (enumerated)  (S) — FR-1.4
- **AC1** `docs/architecture.md`: Lifecycle is the sole state authority; Momo is
  a policy/intent client; current direct provider transitions are labeled legacy;
  MCP/heartbeat deferrals and gateway-PM versus scrum-master distinctions remain.
- **AC2** `docs/index.md` + `docs/project-overview.md` carry the corrected language + promotion framing (verified: no `skillex` path, no "undecided").
- **AC3** `llr` recency check shows the docs are the most recently mutated (truth compass).

---

## Epic 2 — Minimal install + the demo  ·  MVP  ·  **Pillar #1 milestone (comes FIRST)**

**Goal:** One command installs the proven policy skill into a target repo; on a
revenue product it selects legal work, delegates/reviews, submits
intent/evidence, and renders Lifecycle's authoritative result. No generic spec
or fanout engine is required here.

### S2.0 — Record the current-policy demo  (S) — brief §6
- **AC1** The existing skill may be recorded triaging, delegating, and reviewing,
  but any direct move to `completed` is labeled legacy current behavior and is
  not target lifecycle acceptance.
- **AC2** The recording shows a `decision.recorded` event landing in `bloodbank-events.jsonl` with pillar basis.
- **AC3** The "sellable slice" narrative no longer depends on E1–E2 landing.

### S2.1 — Minimal `momo install`  (M) — FR-4.2, FR-4.4
- **AC1** `momo install <repo>` drops the **proven Claude skills-tree** (the payload that already renders and runs) into the target repo — **no generic-master projection**.
- **AC2** Idempotent; resolves the nearest-ancestor `.project.json`; a second run is a clean no-op/update.
- **AC3** After install, a recorded decision lands in the **exact** `_bmad-output/implementation-artifacts/bloodbank-events.jsonl` path the target repo's Hermes sentinel reads (create the dir if absent).

### S2.2 — `momo doctor` hard prereq gate  (M) — FR-2.3, NFR-3
- **AC1** `momo doctor` checks local runtime, PJangler identity, provider
  projection, Bloodbank reachability/schema compatibility, Lifecycle health,
  snapshot/command versions, and the caller's capability grant.
- **AC2** It **refuses to report "ready"** until green; `record-decision.py` exit-3 (bus behind) surfaces as a visible warning, not a swallowed degrade.
- **AC3** A conformance guard fails if a target path directly invokes a provider
  transition, derives legal state locally, or emits an unregistered contract.

### S2.3 — Real shared lock for WIP=1  (M) — NFR-1 *(review: TOCTOU race vs Hermes 60s timer)*
- **AC1** Interactive Momo takes the sentinel's `flock` (or writes an `interactive-hold` marker the sentinel's cheap bash gate honors and **skips on**) — mutual exclusion, not politeness.
- **AC2** A simulated concurrent tick produces neither two workers nor two
  effective commands; repeated command IDs return the original result.
- **AC3** Documented: deferring E5 does not defer this coexistence race — it is
  live the instant Momo installs into a Hermes-managed project.

### S2.4 — Demo on the revenue product  (S) — Revenue + Lifecycle Gates
- **AC1** `momo install` into the chosen revenue product → Momo chooses a legal
  frontier item, delegates/reviews, submits intent/evidence, and renders the
  authoritative resulting state.
- **AC2** The demo proves version/provenance, capability validation, idempotency,
  and no direct provider write. MOMO-on-MOMO remains excluded.
- **AC3** The demo is re-recorded against the installed component.

---

## Epic 3 — House-norm packaging  ·  post-demo polish  ·  Pillar #4

**Goal:** Bring the package up to the toad/pjangler house norm — **after** the demo (Pillar #4 is the lowest-priority pillar; it must not front-run the Pillar #1 milestone).

### S3.1 — Two-bin TS/Node package  (L) — FR-2.1
- **AC1** `@delorenj/momo`, ESM, bins `momo` + reserved `momo-mcp`, deps `@modelcontextprotocol/sdk` + `commander` + `zod`, `esbuild`→`dist/`, mirroring toad/pjangler.
- **AC2** `momo --help`/`--version` run from `dist/`; `--version` derives from manifest/git tag (no literal).
- **AC3** The reserved `momo-mcp` bin ships with the **executable D5 guard** (S2.2 AC3) co-located and active from the moment it exists.

### S3.2 — Versioning + mise tasks + clean `mise enter`  (M) — FR-2.2, NFR-7
- **AC1** `mise run build`/`test` work; `version:*` managed block preserved; `package.json` added to `.mise/version-files.conf`; `version:check` passes.
- **AC2** `mise enter` succeeds end-to-end: `op inject` produces `.env`, `PLANE_<WS>_API_KEY`→`PLANE_API_KEY` resolves (executable check).
- **AC3** Close the scaffold gaps (`codegraph.sh`/`hindsight-setup.sh` missing, no `AGENTS.md`, `agents/` on `_.path`) so `mise enter` is clean.

---

## Epic 4 — Generic spec + fanout + second adapter  ·  post-MVP  ·  Pillar #3 (the SECOND occurrence)

**Goal:** *Now* that a real second CLI target exists, build the generic-spec→many-dialects seam — the Rule-of-Three-honest place for it.

### S4.1 — Author the generic master spec  (M) — FR-3
- **AC1** A `role.yaml`-shaped machine contract (repo, role/kind, agent_id, ticket_provider binding, bloodbank producer/**subscribe** subjects, memory bank = slug, model = inherit) that **projects onto** Hermes `role.yaml` — validated against the **actual** `hermes-agent-template/template/role.yaml.jinja` fields.
- **AC2** The emitted **decision type stays 5-token** (`bloodbank.v1.repo.decision.recorded`, slug in `data.repo`); repo/agent_id appear **only** in subscribe subjects, never in the emitted type (guard against the invalid 6-token form).
- **AC3** A `SOUL.md`-shaped file **references `PILLARS.md`** (asserted: not inlined) and carries the tone knob; flip the PILLARS wiring-checklist row here (where the spec actually exists).

### S4.2 — Extract/vendor Toad's fanout engine  (L) — FR-4.1
- **AC1** Correct manifest: `engine.ts` **+ `spec.ts` + `targets.ts` + `util/deterministic.ts` + `adapters/*`** (the {engine,targets} list was incomplete).
- **AC2** Add a **golden-output test to Toad's fanout first** (Toad has zero tests), so "Toad still builds/passes" is machine-checkable, not a bare typecheck.
- **AC3** Decide the boundary (vendor-with-attribution vs. shared workspace package) and reconcile `loadSpec` with Momo's master schema (or replace `spec.ts` with Momo's loader). Record as the Rule-of-Three decision.

### S4.3 — Second dialect adapter + `fanout sync`/`check`  (M) — FR-8.1, FR-4.3
- **AC1** A **file-render** dialect (OpenCode command or Codex AGENTS.md) renders from the **unchanged** master; if a change was needed it's a superset addition, recorded.
- **AC2** The non-Claude carrier's `record-decision` emits the **correct** `actor.cli`/`provider` (S1.2 AC2 parameterization proven here).
- **AC3** `momo fanout sync` regenerates all dialects; `momo fanout check` fails on a hand-edited generated copy (drift gate, now meaningful with ≥2 dialects).

---

## Epic 5 — Autonomous twin (Hermes adapter)  ·  DEFERRED / GATED  ·  Pillar #1 gate

**Goal:** Momo becomes a Hermes PM client — the same legal-work selection and
intent loop on a timer, never a second lifecycle reconciler.
**Gate:** manual loop validated (E2) **and** a revenue product needs autonomy.

### S5.1 — Hermes adapter (NET-NEW provisioning bridge)  (L)
- **AC1** Named twin role decided and recorded: most likely **pm + paired scrum-master** (the interval heartbeat is the **scrum-master** role's `continuous-ticket-sentinel`, per research — *not* the gateway pm).
- **AC2** The Hermes adapter is **net-new** (renders `role.yaml` + `SOUL.md` **and** shells out to `copier.yml`'s `00..99` scripts) — **not** a file-render like the Toad dialects; scoped separately from S4.3.
- **AC3** The adapter **neutralizes honcho** (Hermes' native per-agent memory) so the twin uses **only** the shared Hindsight bank (= `project_slug`); verify no honcho store is created.
- **AC4** The provisioned twin **strips inherited Slack/Telegram/Discord creds** and has its own identity (agent_id, socket) — verify no parent-socket hijack; binds to the **existing** MOMO board (no new board).

### S5.2 — Lift the heartbeat trigger  (L)
- **AC1** `continuous-ticket-sentinel.sh` is the timer trigger over the **already-reconciled** single pass definition (S1.5).
- **AC2** Liveness keys off process markers + `last_activity_at` (**never** state-file mtime); cooldowns/lock preserved.
- **AC3** Interactive Momo and the twin share Lifecycle command semantics without
  contradiction (idempotency/version checks plus the S2.3 WIP lock).

---

## Epic 6 — MCP proxy server  ·  DEFERRED / GATED  ·  Rule of Three (2nd consumer)

**Goal:** A thin TS MCP exposing coarse PM/EM reads and Lifecycle intent commands.
**Gate:** a second consumer needs programmatic board access beyond the skill.

### S6.1 — Thin proxy over the normalized contract  (L) — D5
- **AC1** Verbs separate snapshot/frontier reads, observations/comments,
  delegation/review evidence, idempotent intent submission, and decision
  provenance. Provider creation remains PJangler's boundary.
- **AC2** State-changing verbs delegate to the Lifecycle command client through
  Bloodbank. Provider adapters may serve projection reads only.
- **AC3** Trello backend already consolidated (S1.4 AC3) — no third path introduced.

---

## Cross-cutting definition of done

Every story: ACs met and demonstrated; consequential judgment calls recorded via
`record-decision.py`; decision events never enact transitions; legal work comes
from an authoritative versioned frontier; state-changing intent goes only through
Lifecycle; no code is edited by Momo itself; WIP=1 is held; docs stay honest.

---

_Generated as part of the Momo planning lifecycle (BMAD-style). v3 incorporates
the approved 2026-07-18 lifecycle-authority correction; the vertical slice is not
implemented._
