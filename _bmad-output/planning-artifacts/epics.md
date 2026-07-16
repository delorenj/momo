# Momo — Epics & Stories

**Date:** 2026-07-16
**Author:** Momo (acting PM, on Jarad's behalf)
**Companion docs:** [product-brief.md](./product-brief.md) · [PRD.md](./PRD.md) · [../../docs/architecture.md](../../docs/architecture.md)

**Sequencing principle:** ordered by shortest path to a demoable/sellable slice (Pillar #1), refereed by Rule of Three. **E0–E3 = MVP.** E4 validates the seam; E5–E6 are deferred/gated.

**Acceptance criteria** are written to pass Momo's own triage rubric (non-empty · testable · enumerated · FR-linked), so this backlog is self-dogfooding.

**Story sizing:** S ≈ ≤½ day · M ≈ ½–1 day · L ≈ 1–2 days (solo).

---

## Epic 0 — Board bring-up & reconciliation  ·  MVP enabler  ·  Pillar #2

**Goal:** Momo can run its own MOMO board. Unblocks dogfooding everything else.
**Why first:** `.project.json` has `board_id: ""` and `state: planned` — Momo literally cannot drive its own board until this is healed.

### S0.1 — Implement/confirm `board_id` self-heal  (M) — FR-5.1
- **AC1** Given `.project.json.ticket_provider.board_id` is empty, running board resolve queries the `33god` workspace and matches the board by **exact** name (`MOMO`/project identifier), not fuzzy.
- **AC2** On a unique match, `board_id` is backfilled into `.project.json` and a `bloodbank.v1.repo.decision.recorded` event is emitted with `data.basis` citing the relevant pillar slug(s).
- **AC3** On zero or multiple matches, the flow **fails loud** (no guess) and surfaces the candidates for a human decision.
- **AC4** Resolution goes through `momo-board.sh` → `tp` only (verified: no direct Plane API call in the path).

### S0.2 — Bootstrap the MOMO board & active milestone  (S) — FR-5.2
- **AC1** The MOMO Plane board exists (or is created via Toad/pjangler, **not** Momo — boundary D6) and `board_id` is populated.
- **AC2** An active milestone/cycle exists to hold the MVP epics.
- **AC3** `momo-board.sh resolve` and `active_milestone` return the correct board/milestone.

### S0.3 — Seed this backlog onto the board  (M) — FR-5.2
- **AC1** Every MVP story (E0–E3) is created as a Plane issue in `backlog`/`unstarted` with title, description, and enumerated ACs copied from this file.
- **AC2** Epics are represented (as Plane epics or a label) and each story links to its epic.
- **AC3** Seeding is idempotent (re-running does not duplicate issues).
- **Gate:** live board writes happen only on explicit go-live (external action).

---

## Epic 1 — Promote the skill (SSOT)  ·  MVP  ·  Pillar #3

**Goal:** The proven skill becomes the component's single source of truth in `33GOD/momo`, behavior unchanged.

### S1.1 — Resolve the SSOT-drift question  (S) — FR-1.1
- **AC1** Diff `33GOD/skills/momo` against any other `momo` skill copy on disk; document which is canonical.
- **AC2** Record the SSOT decision as a `decision.recorded` event with basis.
- **AC3** `docs/` and BRAINDUMP references to the stale `~/code/skillex/all-skills/momo` path are corrected or annotated.

### S1.2 — Lift the skill into the repo  (M) — FR-1
- **AC1** `SKILL.md`, `references/*`, `templates/*`, and `scripts/{momo-board.sh,record-decision.py,momo-config.py,providers/trello.py}` are present in the `33GOD/momo` repo under the agreed layout.
- **AC2** No behavior change: the lifted scripts run and produce identical output to the source (spot-verified on `resolve`, `list_issues`, a dry `record-decision`).
- **AC3** Scripts remain stdlib-only (python3 + bash); no new deps introduced.

### S1.3 — Verify contract byte-correctness post-lift  (M) — FR-1.2
- **AC1** A recorded decision validates against `bloodbank/schemas/bloodbank/v1/repo/decision.recorded.v1.json`.
- **AC2** The event type is exactly 5 tokens with slug in `data.repo` (the 6-token form is asserted-against).
- **AC3** `tp`/`trello.py` return the 7 normalized ops over the 5 states unchanged (contract test or manual check documented).

### S1.4 — Wire PILLARS reference & correct docs  (M) — FR-1.3, FR-1.4
- **AC1** The Momo agent spec/soul (once drafted in E3) **references** `PILLARS.md`; the PILLARS wiring-checklist row for Momo flips to ✅ with the reference point recorded.
- **AC2** `docs/architecture.md` is corrected: MCP proxy marked **deferred** (not core), language decided (two-tier), and the **D5 correction** (never proxy Python Plane MCP; delegate to `tp`) stated explicitly.
- **AC3** `docs/index.md` + `docs/project-overview.md` updated for consistency; `llr` recency sanity-checked.

---

## Epic 2 — Component wrapper & versioned package  ·  MVP  ·  Pillar #4

**Goal:** `@delorenj/momo` — a TS/Node two-bin package matching the toad/pjangler house norm, wrapping the Python/Bash glue.

### S2.1 — Scaffold the two-bin TS package from toad's skeleton  (L) — FR-2.1
- **AC1** `package.json` = `@delorenj/momo`, `type: module`, two bins (`momo`, `momo-mcp` reserved), deps `@modelcontextprotocol/sdk` + `commander` + `zod`.
- **AC2** `build.mjs` (esbuild) produces `dist/`; `momo --help` runs from the built CLI.
- **AC3** Package layout mirrors toad/pjangler (`src/`, `src/mcp-server.ts` placeholder, `dist/`).

### S2.2 — Wire mise tasks & versioning  (M) — FR-2.2, NFR-7
- **AC1** `mise run build`, `mise run test` work; the existing `version:*` managed block is preserved.
- **AC2** `momo --version` derives from `package.json`/git tag at runtime (no hardcoded literal); `mise run version:check` passes.
- **AC3** `package.json` is added to `.mise/version-files.conf` so version parity is enforced across manifest + git tag.

### S2.3 — TS↔glue boundary  (M) — FR-2.3, NFR-2
- **AC1** The CLI shells out to `momo-board.sh`/`record-decision.py` (no reimplementation of board/decision logic in TS).
- **AC2** Runtime deps (python3, bash) are documented in the README and checked by `momo doctor`.
- **AC3** `momo doctor` reports install health (glue present, deps found, `.project.json` resolvable).

---

## Epic 3 — Fanout install + Claude adapter  ·  MVP  ·  **Demo milestone**  ·  Pillar #1

**Goal:** One command installs Momo into any CommonProject repo; behavior identical to today's skill.

### S3.1 — Extract Toad's fanout engine into a shared seam  (L) — FR-4.1
- **AC1** `toad/src/fanout/{engine.ts,targets.ts}` + adapters are consumed by Momo via a shared lib or vendored-with-attribution — **no second, drifting fanout engine** exists.
- **AC2** The extraction is recorded as a decision (Rule of Three, 2nd occurrence) with basis.
- **AC3** Toad still builds/passes after the extraction (no regression to the cousin component).

### S3.2 — Author the generic master spec  (M) — FR-3
- **AC1** A `role.yaml`-shaped machine contract exists (repo, role/kind, agent_id, ticket_provider binding, bloodbank producer/subjects, memory bank = slug, model = inherit) that **projects onto** Hermes `role.yaml`.
- **AC2** A `SOUL.md`-shaped file exists that **references `PILLARS.md`** (asserted: PILLARS content is not inlined) and carries the tone knob + Momo behavior contract.
- **AC3** The master is the only hand-edited source; generated copies carry a "do not edit" provenance header.

### S3.3 — Claude Code skills-tree adapter + `momo install`  (L) — FR-4.2, FR-4.4
- **AC1** `momo install <repo>` renders the generic master into a `.claude/skills/momo` tree (+ `.agents` if applicable) in the target repo.
- **AC2** Install is idempotent and resolves the nearest-ancestor `.project.json`; a second run is a no-op/clean update.
- **AC3** The installed skill runs a board loop in the target repo (triage→delegate→review) — verified end-to-end on a scratch CommonProject.

### S3.4 — `fanout sync` / `fanout check` drift gate  (M) — FR-4.3, NFR-5
- **AC1** `momo fanout sync` regenerates all dialect copies from the master.
- **AC2** `momo fanout check` exits non-zero when a generated copy has been hand-edited (drift), zero when in sync — usable as a CI gate.
- **AC3** A deliberately-edited generated copy is detected by `check` in a test.

### S3.5 — MVP demo & decision record  (S) — PRD §7
- **AC1** End-to-end demo recorded: `momo install` into a CommonProject → it triages, delegates to a subagent, reviews, and moves an issue to `completed`, emitting a `decision.recorded` event.
- **AC2** The event trail (`bloodbank-events.jsonl`) shows the decision with pillar basis.
- **AC3** A short DEMO.md (or asciinema) captures the flow for the "sellable slice" narrative.

---

## Epic 4 — Second CLI adapter  ·  post-MVP  ·  Pillar #3 (seam validation)

**Goal:** Prove the generic-spec seam with a real second call-site.

### S4.1 — Add one more dialect adapter (OpenCode | Codex | Hermes)  (M) — FR-8.1
- **AC1** `momo install` renders the chosen second dialect from the **unchanged** generic master.
- **AC2** No master-spec change was required to add the dialect (seam validated); if a change was needed, it's a superset addition, recorded as a decision.
- **AC3** `fanout check` covers the new dialect.

> **Decision to make when we get here:** which dialect is the highest-leverage second target — Hermes (unifies with the autonomous fleet) or a second interactive CLI. I lean **Hermes** (it also unlocks E5), pending the revenue-product context.

---

## Epic 5 — Autonomous twin (heartbeat via Hermes adapter)  ·  DEFERRED / GATED  ·  Pillar #1 gate

**Goal:** Momo becomes a Hermes PM — the same reconcile loop on a timer.
**Gate:** manual loop validated (E3) **and** a revenue product needs autonomy.

### S5.1 — Hermes adapter: render spec → soul+role  (L) — brief §7
- **AC1** The Hermes adapter renders Momo's generic master into a valid `SOUL.md` + `role.yaml` for `hermes-agent-template`.
- **AC2** Provisioning shells out to the existing `copier.yml` + `00..99` scripts (no reimplementation of GH-runtime/systemd/bloodbank plumbing).
- **AC3** The provisioned twin appends to `~/.hermes/agents-registry.yaml` and binds to the **existing** MOMO board (no new board).

### S5.2 — Lift the heartbeat trigger  (L)
- **AC1** `continuous-ticket-sentinel.sh` is lifted as the timer trigger over the **same** reconcile-pass definition the interactive Momo uses.
- **AC2** Liveness keys off process markers + `last_activity_at` (never state-file mtime); cooldowns/lock preserved.
- **AC3** Interactive Momo and the autonomous twin share one pass definition (single source), proven by both driving the board without contradiction (WIP=1 respected).

---

## Epic 6 — MCP proxy server  ·  DEFERRED / GATED  ·  Rule of Three (2nd consumer)

**Goal:** A thin TS MCP exposing ~8–10 coarse PM verbs, delegating to `momo-board.sh`/`tp`.
**Gate:** a second consumer needs programmatic board access beyond the skill.

### S6.1 — Thin proxy over the normalized contract  (L) — brief §7, D5
- **AC1** The MCP exposes coarse verbs (`board_resolve`, `board_active_milestone`, `board_list_issues`, `issue_get`, `issue_comment`, `issue_transition`, `board_create`, plus composites `triage_ticket`, `pick_next`, `record_decision`) — **not** the raw 61+90 Plane/Trello tools.
- **AC2** Every verb delegates to `momo-board.sh`/`tp`/`trello.py` — **asserted: no call into the Python Plane MCP** (D5), no divergent board resolution.
- **AC3** The Trello backend is consolidated to **one** implementation before shipping (Rule of Three; no third Trello path).

---

## Cross-cutting definition of done

Every story: ACs met and demonstrated; any consequential judgment call recorded via `record-decision.py` with pillar basis; board updated through `tp` only; no code edited by Momo itself (delegated); docs kept honest (`llr`-checked).

---

_Generated as part of the Momo planning lifecycle (BMAD-style)._
