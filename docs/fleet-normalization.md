# Hermes Fleet Normalization + Momo/Hermes/Toad Unification

**Status:** analysis complete (grounded on disk + systemd, 2026-07-21). Scripts pending 2 gating decisions.
**Scope:** the 22 deployed Hermes PM agents, their runtimes/services, and how Momo/Toad unify them.
**Method:** 5-dimension parallel recon against live systemd units + on-disk runtimes (docs treated as stale).

> Home note: this doc lives in `momo/docs/` because Momo is the SSOT hub for the PM
> unification, but it is fleet-wide (touches hermes-fleet, toad, pjangler, skillex).
> Move it if a better home emerges.

---

## 0. Decisions that gate the mutating scripts — **LOCKED 2026-07-21**

| # | Decision | Choice |
|---|---|---|
| **D1** | Naming token | ✅ **`<repo>-pm` (hyphen)** — the live convention. The sweep fixes *deviations* only (james-brennan→jamesbrennan, carrie, bare-layout). Underscore stays only in the telegram handle `<repo>_pm_bot`. |
| **D2** | "git-tracked runtime" | ✅ **Pure-local** — unstage the gitlink from the project repo **and** retire the runtime's own checkpoint `.git`. Runtime becomes pure local state; per-agent memory durability relies on the Hindsight bank. Also retires the checkpoint services (no more `git push`), fixing the 4 failures. The `github.com/delorenj/agent-hm-*-pm` remotes are left intact (recoverable), just no longer pushed to. |
| **Seq** | Build order | ✅ **Degit + debris cleanup first**, then rename, then templatize, then the Hermes-adapter unification. |

**Corollary of D2:** pure-local runtime means the `-checkpoint.service/.timer` units are dead weight and the checkpoint half of `heartbeat.sh` becomes a no-op — the cleanup retires the standalone checkpoint units and the reconcile/autonomous half of heartbeat stays for the 4 autonomous agents.

**Safety confirmed (why pure-local degit is safe fleet-wide):** `checkpoint.sh:15` is `[[ -d .git || -f .git ]] || exit 0` and heartbeat's `maybe_checkpoint()` is best-effort ("never fails the heartbeat"). So after degit, checkpoint.sh is a clean exit-0 no-op and the autonomous reconcile tick is untouched — degitting even the 4 heartbeat agents (candystore, pjangler, james-brennan, slowburns) cannot break their loop. Degit also *fixes* the `hermes-agent-pm-checkpoint` failure (no more `git push` on a diverged runtime).

### Delivered scripts (in `hermes-agent-template/scripts/`)
- **`degit-runtime.sh`** — per-repo pure-local degit (item 1b). Run from a repo root (or `--root`). Dry-run default, `--apply`, `--force` (discard unpushed local-only checkpoint history). `-f` on the index removal handles staged-but-uncommitted submodules.
- **`fleet-prune-debris.sh`** — fleet-wide debris prune: removes disabled stale units + `.bak` cruft, retires now-dead checkpoint units for already-pure-local agents, reports the rest (failed/running-redundant) as MANUAL. Dry-run default.

### Execution status (2026-07-21) — item 1b + debris cleanup DONE
- **All 22 PM runtimes are pure-local** (verified: gitlink=0, ignored=Y, no runtime `.git`, across all scattered repo roots).
- **0 checkpoint units remain** — all retired; the `hermes-agent-pm-checkpoint` failure is gone.
- Pruned: 3 disabled stale gateways, 3 `.bak-tiller` files.
- **All live daemons untouched** — 21 consumers / 20 gateways active (the only 3 down — keepy-money consumer, bloodbank + hermes-agent gateways — were already dead pre-change). Remaining failed: 2 `delonet-company-reporter` (non-PM archetype, out of scope).
- Project-repo degit changes are committed locally per repo where clean (sidepiece); the rest are staged/unstaged in each project repo for the owner to commit. Working trees, `.env`, `state.db` all preserved.
- **Item 1a (rename) deferred** at user request (needs interactive telegram/BotFather work).

### Item 1c (templatize) + Task 4 (unification) — foundations built (2026-07-21)
**Task 3 (templatize) — pack live + tool ready:**
- Built `skillex/packs/hermes-base/0.18.2/` — 18 pristine base skills (7.0M), MANIFEST regenerated from the copy, guard confirms **byte-parity with upstream**. Inert until wired.
- `hermes-agent-template/scripts/hermes-runtime-templatize.sh` (dry-run default): WIRE (append pack to `config.yaml external_dirs`, additive/comment-safe) + RECONCILE (rm byte-identical base copies; **patch-capture + keep** diverged; leave overlay-adds). Validated on voxxy: 5 identical / 12 diverged / 11 overlay.
- `hermes-base-guard.sh` (in the pack) forbids in-place base edits — the exact hole that forked 14/18 dirs.
- **Verified precedence caveat:** local overlay wins the prompt *index*, but `skill_view` *refuses* a divergent local↔pack name collision ("Ambiguous skill name") — so base and overlay must end name-disjoint, which removing the identical copies achieves.

**Task 4 (unification) — SSOT foundation placed (new files in `momo/`):**
- `momo/spec/momo-agent.spec.yaml` — the identity-agnostic behavioral SSOT (roles, charter, prime directives, pillars/lifecycle pointers, memory doctrine, `<slug>-momo` decision identity).
- `momo/adapter/{render_agent.py, config.overlay.yaml, RENDER_MAP.md, record-decision.fix.md}` — the Hermes adapter (renders `role.yaml`/`SOUL.md` from spec×identity via the existing copier template; honcho-neutralization overlay verified against hermes source).
- `momo/lifecycle/{lifecycle.v1.yaml, CHANGELOG.md, README.md}` — the one versioned Lifecycle state machine (9 phases → 5 tp bands; per-repo labels move to the `tp` Strategy).
- **Applied safe edits:** `record-decision.py` urn fix (`hermes://agent/<slug>-momo`, `decided_by=momo` preserved — verified); PILLARS wiring row ticked (spec references `PILLARS.md`, not copied); stale `skillex/all-skills/momo` refs fixed in BRAINDUMP + PILLARS.

**Staged (risky live-fleet — pilot + confirm before rollout):** wire pack to 22 configs → reconcile `--apply` (+ triage 12 diverged) · deploy the adapter (render + honcho-neutralize live agents) · repoint the lifecycle mirror (`board-clearing-loop.md`, `SKILL.md`) · per-repo `workflow.yaml` migration · sync `skills/momo` ← SSOT.

**Templatize pilot findings (2026-07-21):**
- **The rollout needs per-agent prep — there is no clean one-shot agent.** The 19 new-gen agents have `external_dirs` but carry **diverged** base skills (voxxy: 12) that must be triaged (discard-drift / promote-to-pack / rename-overlay) before wiring; the 3 bare agents (candybar, pjangler, hermes-agent) have **no `skills.external_dirs` block** at all and need one provisioned first.
- **Precedence caveat is real:** wiring while a diverged (or even identical, pre-delete) base local remains makes `skill_view` return "Ambiguous skill name". So the script now **reconciles-to-name-disjoint then wires**, and **refuses to wire (no deletions) while any diverged base local remains** — safe on every agent.
- **Bug caught + fixed:** an early version's `wire` silently "succeeded" on a bare config (a `set -e`-in-function gotcha) and deleted pjangler's 18 base skills; restored them from the pack (byte-identical) and hardened `wire_cfg` to fail-before-delete. voxxy was never mutated.

### Templatize EXECUTED — per-skill, scoped-name (2026-07-23)
Reworked the tool to **`hermes-runtime-templatize.py`** (per-SKILL, since 14/18 base dirs are categories holding 73 sub-skills; it mirrors hermes `iter_skill_index_files` exactly — excludes `.archive`/support dirs). **Policy (your call):** identical base sub-skill → delete (resolve from pack); **overwritten → scoped-name override** (rename dir + frontmatter `name:` → `<name>-<slug>`, promoting it to an unambiguous agent-scoped copy); agent-adds → untouched.
- **18 of 22 agents deduped + `verify: CLEAN` (name-disjoint)**, services unchanged (21/20), no new failures. Many agents shed all 73 duplicated base skills (now resolve from the one pack); a few kept edits as scoped copies (delodocs kept 45 as `*-delodocs`, nautilus_trader/33god 3 each, etc.).
- **4 bare agents BLOCKED** (candybar, delocontainers, drumjangler, pjangler) — no `skills.external_dirs` key; they need a skills block provisioned before dedup (a config decision — and whether to also give them + bloodbank the mainline `global/.system` + `bmad` dirs for fleet consistency).
- Runtime changes live on disk only (runtimes are pure-local by D2 — no git). The tool is committed; the `hermes-base-guard.sh` is still dir-level and should be reworked to per-skill (the tool's `verify` does per-skill now).

---

## 1. Fleet census — 22 deployed PM agents

Authoritative runtime path = `HERMES_HOME` in each `hermes-<repo>-pm-consumer.service`.
**Repos are scattered** — NOT all under `~/code/33GOD`. Always resolve from the unit, never assume a path.

| repo | runtime root | size | runtime git | telegram (active) | svc gen | deviation |
|---|---|---|---|---|---|---|
| 33god | `~/code/33GOD` | 253M | gitlink | — | checkpoint | monorepo root PM |
| bloodbank | `~/code/33GOD/bloodbank` | 174M | ignored | — | checkpoint | old-gen debris (`bin/`,`provision.sh`); gateway DEAD |
| candybar | `~/code/33GOD/candybar` | 41M | **untracked/dirty** | — | checkpoint | bare pre-role.yaml; **checkpoint FAILED** |
| candystore | `~/code/33GOD/candystore` | 42M | ignored | — | **both** ckpt+hb | transitional (redundant checkpoint) |
| coachingagentframework | `~/code/CoachingAgentFramework` | 61M | gitlink | — | checkpoint | |
| delocontainers | `~/docker` | 98M | ignored | — | checkpoint | off-tree (`~/docker`) |
| delodocs | `~/code/DeLoDocs` | **769M** | **no git repo** | — | checkpoint | owning repo has no `.git` |
| drumjangler | `~/code/drumjangler` | **3.0G** | gitlink | — | checkpoint | HERMES_HOME via `~/.hermes/profiles` **symlink**; bloat |
| hermes-agent | `~/.hermes/hermes-agent` | 94M | **untracked nested** | — | checkpoint | **seed agent** (owns shared `.venv`); **checkpoint FAILED**; gateway DEAD |
| holocene | `~/code/33GOD/holocene` | 101M | gitlink | ✅ HolocenePMBot | checkpoint | |
| intelliforia-voice-agent | `~/code/intelliforia-voice-agent` | 38M | gitlink | ✅ | checkpoint | **redundant 2nd gateway** (legacy unit) |
| jacksnaps | `~/code/jacksnaps` | 97M | gitlink | — | checkpoint | |
| james-brennan | `~/code/AutomaticAI/Prospects/JamesBrennan` | 106M | ignored | ✅ AirMarshalCarlinBot | **heartbeat-only** | **name mismatch**: unit `james-brennan` vs role.yaml `jamesbrennan-pm` |
| keepy-money | `~/code/KeepyMoney` | 39M | gitlink | ✅ KeepyMoneyBot | checkpoint | 3 `.bak-tiller` unit backups (cruft) |
| nautilus_trader | `~/code/nautilus_trader` | 115M | gitlink | — | checkpoint | underscore repo; pm/ polluted w/ ~20 kraken PNGs |
| pjangler | `~/code/pjangler` | 64M | **no git repo** | — | **both** ckpt+hb | bare pre-role.yaml |
| sidepiece | `~/code/sidepiece` | 80M | gitlink | — | checkpoint | `role.yaml model.name='plane'` (buggy field) |
| skillex | `~/code/skillex` | 19M | ignored | — | checkpoint | smallest (good reference) |
| slowburns | `~/code/slowburns` | 66M | ignored | ✅ SlowBurnsBot | **heartbeat-only** | newest gen |
| tonnybox | `~/code/TonnyBox` | 418M | gitlink | ✅ TonnyBoxPMBot | checkpoint | |
| voxxy | `~/code/voxxy` | 172M | gitlink | ✅ VoxxyPMBot | checkpoint | |
| zshyzsh | `~/.config/zshyzsh` | 54M | gitlink | ✅ DrZshyZshBot | checkpoint | off-tree; **fullest role.yaml** (use as template ref) |

**Git-tracking split:** 12 gitlink submodules · 6 gitignored · 2 no-repo (delodocs, pjangler) · 2 untracked/dirty (candybar, hermes-agent).
**Active telegram tokens:** 8 (holocene, intelliforia, james-brennan, keepy-money, slowburns, tonnybox, voxxy, zshyzsh). The other 14 declare a `bot_username` but have no live token — telegram rename only matters for those 8.

### 7 naming/looping generations (oldest → newest)
1. **Named-persona** (`carrie` → @DrDumplyBot; `~/.hermes/profiles/<name>`; no repo binding).
2. **Seed/bare** (pre-role.yaml; `pm/` has only `runtime/`; identity inside runtime): hermes-agent, candybar, pjangler.
3. **old-agents-hermes** (`agents/hermes/{bin,provision.sh,runtime}`): leftover in bloodbank.
4. **generic-gateway** (`hermes-gateway[-hash|repo].service`, defunct `venv/` path): all stale/disabled except the intelliforia one which double-runs.
5. **reponame-pm mainline** (role.yaml contract + `checkpoint.timer` + gitlink runtime): the current bulk.
6. **heartbeat gen** (fused reconcile+checkpoint): (a) transitional keep-both (candystore, pjangler); (b) checkpoint-dropped heartbeat-only (james-brennan, slowburns) ← newest.
7. **non-PM reporter archetype** (`delonet-company-reporter-*`: cron-tick/watchdog/artifact-bridge) — *not a PM, out of scope.*

### Debris to prune (NOT part of the 22)
- `hermes-carrie-{backend,telegram-gateway}` — old named persona (decide keep-as-special vs retire).
- `hermes-gateway.service`, `hermes-gateway-de01182b`, `hermes-gateway-intelliforia-voice-agent`, `hermes-dashboard-delodocs-pm` — stale/redundant gateways (remove).
- `hermes-keepy-money-pm-*.bak-tiller-20260707153852` (×3) — backup cruft (remove).
- `hermes-delonet-company-reporter-*` — different archetype (investigate/repair separately).
- **4 FAILED units:** candybar-pm-checkpoint (missing script), hermes-agent-pm-checkpoint (git push non-ff on diverged submodule), delonet checkpoint + watchdog.
- **2 DEAD PM gateways:** bloodbank, hermes-agent (restart or confirm intentional).

---

## 2. Why 3–4 services per agent — and the collapse (your Q1d)

**What the units actually are:**
| unit | type | job |
|---|---|---|
| `-gateway` | long-running daemon | `hermes gateway run` — messaging (Telegram), sessions, dispatcher, **internal cron scheduler**, ingests the bloodbank inbox, drives turns |
| `-consumer` | long-running daemon | ~40-line NATS→file bridge: subscribes repo+agent subjects, writes each msg to `runtime/bloodbank-inbox/` |
| `-checkpoint` | oneshot + timer | hourly `git add/commit/push` of the runtime submodule (no-op on clean tree) |
| `-heartbeat` | oneshot + timer | ~1min flock+cooldown; reconcile off→checkpoint only, on→spawns `hermes chat --max-turns 90` then checkpoints (**supersedes** the checkpoint timer) |

**You're basically right — it can be ~one unit — but the survivor is the GATEWAY, not the consumer.** The three exist today for three *runtime-isolation* reasons, none of which needs a separate systemd **unit**:
1. **Restart isolation** — a NATS crash restarts a cheap bridge instead of bouncing the stateful gateway mid-turn.
2. **Timer vs daemon** — checkpoint/heartbeat are periodic; oneshot+`.timer` gives free `Persistent` catch-up + per-run timeout.
3. **Blocking work out-of-band** — the 45-min reconcile chat and the blocking `git push` would stall the gateway loop if inlined.

**Collapse design (`hermes-<repo>-pm.service`, one unit):**
- Consumer's NATS subscription → an **asyncio task on the gateway loop** with reconnect-backoff (deletes the process *and* the inbox-file round-trip, which only exists because they're separate processes).
- checkpoint + heartbeat → **jobs on the gateway's existing internal cron scheduler**.
- The heavy reconcile chat + git push stay a **detached, flock-gated subprocess** (not on the loop).
- **What you'd re-implement in-daemon:** systemd `Persistent` catch-up + per-run timeout kill; you lose independent per-unit failure surfacing.
- **Pragmatic middle ground = 2 units:** fused gateway+consumer daemon **+** one `heartbeat.timer` (keeps systemd catch-up/timeout for the heavy pass). This is exactly where candystore/pjangler are already drifting.

> This is a **hermes-agent harness change** (gateway code + template `70-systemd.sh`), not a one-shot script — it's a roadmap item, not part of the 3 normalization scripts.

**Why checkpoints fail:** (1) candybar → `checkpoint.sh` doesn't exist (bare layout); (2) hermes-agent/delonet → `git push` rejected (diverged submodule, detached HEAD) and this variant doesn't `|| true` like candystore does; (3) delonet watchdog exit-1 is *by design* (it's the alarm). D2=(A) makes 1–2 moot by removing the git push entirely.

---

## 3. The three idempotent scripts (specs)

All: **dry-run by default** (`--apply` to mutate), idempotent (safe to re-run), resolve every path from the unit's `HERMES_HOME` (never assume `~/code/33GOD`), operate only on the 22 live `*-pm-consumer` WorkingDirectories, and skip debris by an explicit allowlist.

### 3a. `hermes-fleet-rename` — normalize an agent to `<repo>-pm`
Identity is **derived, not substring-replaced** (from `copier.yml`): `agent_id=<repo>-<role>`, `display_name=<repo|title> <role|upper≤3 else title>`, `bot_handle=<repo|lower|_>_<role>_bot`, `runtime_repo=agent-hm-<repo>-<role>`, `profile=agent_id`. Recompute all.

Touch points (every place identity is written):
- `role.yaml` (repo, role, agent_id, display_name, profile, telegram.bot_username, plane.identifier, bloodbank.routing.*, producer, runtime.github_*).
- `SOUL.md` + `runtime/SOUL.md` (H1, agent_id, `producer=hermes-agent:<agent_id>`, `source=hermes://agent/<agent_id>`, @handle, routing target `<repo>-dev`).
- `runtime/bloodbank-consumer.py` (AGENT_ID/REPO/ROLE/PRODUCER/SOURCE) — or re-render if placeholders present.
- systemd: unit **filenames** `hermes-<agent_id>-{gateway,consumer,heartbeat|checkpoint}.{service,timer}`, `Description=` lines, `WorkingDirectory`/`HERMES_HOME`/`ExecStart`/log paths, `EnvironmentFile=-%h/.hermes/<agent_id>.env` → `daemon-reload` + re-enable.
- `~/.hermes/agents-registry.yaml` key `agents.<agent_id>` + nested fields.
- `~/.hermes/profiles/<profile>` symlink → `<role_dir>/runtime`.
- runtime GitHub repo `agent-hm-<repo>-<role>` + project `.gitmodules` url.
- **DO NOT touch:** the Hindsight bank (= *repo* name, not agent_id) — memory is per-project.
- **Telegram** (manual, gated — see §5): only the 8 with live tokens, only if the handle changes.

Real work items this catches: `james-brennan`→`jamesbrennan-pm` mismatch; carrie (decide); bare-layout agents missing role.yaml.

### 3b. `hermes-degit-runtime` — remove the runtime from git (run from repo root)
**Layer A (project repo):** ensure `.gitignore` has `agents/hermes/*/runtime/`; if the runtime is a gitlink submodule → `git rm --cached agents/hermes/<role>/runtime`, strip the `[submodule …/runtime]` stanza from `.gitmodules` (delete file if last), `rm -rf .git/modules/agents/hermes/<role>/runtime`.
**Layer B (runtime itself):** ensure the runtime `.gitignore` contract (secrets, caches, sandboxes, logs, pycache). If **D2=(A)** pure-local: also `rm -rf runtime/.git`, set `runtime/.gitignore` = `*`\n`!.gitignore`, and drop the profile-symlink/registry `runtime_repo` coupling.
Idempotent: each step checks state first (already-ignored → no-op).

### 3c. `hermes-runtime-templatize` — dedup to the example-runtime shape
The **only correctly-deduped thing today is the shared venv** (`~/.hermes/hermes-agent/.venv`). Everything else is copied 22× and drifting. Target = 3 physical tiers (see §4). This is the largest script (touches skills resolution) and should land last, on a pilot repo first.

---

## 4. Runtime dedup — shared template + thin per-agent overlay

**Three tiers:**
1. **Shared, read-only, one copy, in no per-agent git:**
   - `~/.hermes/hermes-agent/.venv` (already shared).
   - **NEW** `skillex/packs/hermes-base/<version>/` — the ~28 upstream base skills, version-pinned like the existing `bmad/6.10.2` pack.
   - hook logic (`~/.agents/hooks/*`, `33GOD/.agents/hooks/*` — already shared; per-agent `hooks/` dir is empty/vestigial).
   - the copier template (`hermes-agent-template`: the ONE launcher, `.scripts/*.sh`, `bloodbank-consumer.py`, `config.yaml.j2`).
   - `~/.hermes/{SOUL,USER,AGENTS,MEMORY}.md` global identity base.
2. **Template-rendered per-agent (regenerable, thin):** `hermes` launcher, `.scripts/`, `.runtime-scaffold/`, `config.yaml` — produced by `copier update` from `role.yaml`. **Symlink** immutable infra (launcher, consumer) so a template bump propagates; **render** only files that interpolate identity (`config.yaml`).
3. **Per-agent state (committed if D2=B, else pure-local):** `role.yaml`, `SOUL.md`, `memories/`, `skills/` **overlay only**, `state.db`, `kanban.db`. `.env`/caches/sandboxes/logs gitignored.

**Skill resolution — the crux (memory + base-skills question you raised):**
- **Base skills** → NOT symlinked, NOT copied. Add the shared pack to each `config.yaml` `skills.external_dirs` (the mechanism already exists and is in use for `skillex/.system` + `bmad/6.10.2`). Hermes **merges** the read-only external base with the local writable `skills/` overlay at prompt-assembly time; **local overlay wins on name collision** = per-agent extend/override for free. This is strictly better than a symlinked base, which lets the curator mutate the shared base in-place — exactly how 14/28 skill dirs got polluted.
- **Memory** → two-layer, override-on-conflict, never shared. Base at `~/.hermes/*.md`; each agent's `runtime/memories/` + `runtime/SOUL.md` load on top and win. Durable cross-session knowledge already lives in the per-repo **Hindsight bank**, so `runtime/memories/` stays deliberately small and agent-local.
- **Required behavior change:** the curator edits base `SKILL.md` **in-place** today (the cause of divergence). It must be constrained to write only into the overlay; base improvements go **upstream to the skillex pack** (PR), benefiting all 22 at once.

**Savings:** ~25–35M working-tree/agent from skill/backup dedup; ~30M/agent in git history from de-committing base skills (needs a coordinated `filter-repo`); **~1.2–1.5 GB true duplication fleet-wide**, plus several GB reclaimable from log rotation + `git gc`. (Not counting drumjangler's 3.0G / delodocs' 769M anomalies, which are their own cleanup.)

---

## 5. Telegram bot rename — the manual steps (script-guided)

Telegram bot **@usernames cannot be freely changed** after creation via BotFather; only the **display name** (`/setname`) changes freely. So for the 8 live-token agents, if the handle must change, the script will **pause** and print the exact steps, then read the result back:
1. `/setname` @<bot> → new display name (matches `display_name`). *(always doable)*
2. If the **@username** must change: BotFather can't rename it → either keep the old @username (recommended — it's cosmetic; the token is what matters) **or** create a fresh bot (`/newbot`), grab the new token, and the script swaps `TELEGRAM_BOT_TOKEN` in `runtime/.env` + `bot_username` in `role.yaml`, then restarts the gateway.
3. Script prompts: *"paste the new token (or blank to keep current)"* → writes `.env` → `systemctl --user restart hermes-<agent_id>-gateway`.

Tell me what BotFather actually allows in your account and I'll wire the exact branch.

---

## 6. Momo / Hermes / Toad — your open questions, answered

**Frame (from BRAINDUMP 47–49):** *"all of this is being handled by default by Hermes agents… this is the end state of what I want, had we used this Momo — with a Hermes adapter."* Momo is the **generic behavioral SSOT**; a Hermes PM is **Momo rendered through a Hermes carrier/adapter**. They are **twins over one shared substrate** (same `.project.json`, same `tp` board adapter + 5-state/7-op contract, same Plane board per repo, same Hindsight bank per repo, same Bloodbank decision contract, same WIP=1 + two-gate + reviewer-independence pipeline, same pillars). Momo even invokes Hermes' own close gate (`sentinel/bin/issue-autonomous-review.sh`).

- **(a) Replace the 22 Hermes PMs with Momos?** — **Yes, as convergence, not deletion.** Make Momo the one behavioral spec; turn Hermes into a carrier. Keep the 22 systemd deployments; re-point each PM's forked SOUL behavior to *reference* the one Momo spec. One behavior, two triggers. (This is literally Pillar #3 + Rule-of-Three — "Momo is the Rule of Three made flesh.")
- **(b) Mutually exclusive / either-or per project?** — **Neither. Complementary drivers of one board, gated by a real shared WIP=1 lock.** The per-project choice is the **trigger mix** (interactive-only / autonomous-only / both), not which system. Default: interactive Momo everywhere; enable the Hermes autonomous carrier only where an always-on heartbeat earns its keep (today just 4/22 actually run the sentinel — the other 18 are *reactive*, not self-driving).
- **(c) Enhance Hermes using Momo as the agnostic template?** — **Yes — the keystone move.** Momo = agnostic SSOT (generic spec + codified loop/pipeline + the promoted Lifecycle machine); build the **Hermes adapter** (momo E5) that renders Momo → `role.yaml`+`SOUL.md` and shells out to the copier template, and **neutralizes honcho** so both drivers use only the shared Hindsight bank. Kills 22 near-duplicate forked SOULs (which already drift: sidepiece `model.name='plane'`).

**Toad** = a **single, system-wide, on-demand memory agent** above the per-repo Momos (approved 2026-07-15 "Agent-Native Toad" — a deliberate move *away* from the two-bin TS product). It owns the **one cross-repo Hindsight bank `toad`** (Portfolio Map + Relationship Graph + Custodian Policy), turns a BRAINDUMP/URL into a ProjectIntent, and **operates the canonical pjangler MCP tools** (`pjangler_project_init`, `pjangler_deploy_hermes_agent`, `pjangler_audit/migrate`, …). Hard boundaries: **Toad ships no CLI/MCP of its own**, never proxies pjangler, never calls gh/git/Plane directly. The on-disk `toad-mcp`/`src/fanout`/`dist/` is transitional drift slated for retirement. **Toad births/adopts/audits/migrates projects and deploys their PM; Momo then runs the board** (Momo boundary D6).

## 7. The Lifecycle as a formal entity

Model it as a **State machine (GoF State)**, a triple:
- **Definition (the "class"):** the BMAD ticket-lifecycle workflow (`_bmad/custom/workflows/ticket-lifecycle/workflow.yaml`) — canonical states (Backlog · Triage/Refining/Ready · In Progress · Review/QA · Done + Blocked) + guards (AC rubric = non-empty ∧ testable ∧ enumerated ∧ fr-coverage; qa.max_retries; per-state staleness minutes). `momo/skill/references/board-clearing-loop.md` mirrors this exact machine ("do not invent a different machine").
- **Instance (the live object):** the Plane board — each ticket is a **token** with a current state.
- **Log (the history):** evidence dir + the Bloodbank decision trail (append-only transition log).

**Formalize:** lift `workflow.yaml` out of each repo into **one versioned Lifecycle spec** shipped with the Momo component; keep per-repo label differences in the `tp` normalized-state map (Strategy), not forked machines. Patterns: State + Template Method (fixed per-tick pass, overridable steps) + Strategy/Factory (provider from `.project.json`) + Observer (decision events).

**The agent as driver:** per-repo Momo (or its Hermes carrier) is the **transition-function executor, not the state owner** — the board owns state. Each pass: read the token's state → evaluate guards → fire the allowed transitions (WIP=1) → record each consequential transition as a Bloodbank event. **Interactive Momo and the Hermes heartbeat are interchangeable executors of the same machine over the same instance** — which is *exactly* why the shared WIP=1 lock is mandatory (no double-drive). One tier up, **Toad drives the meta-lifecycle** (project birth→adopt→audit→migrate→retire; instance = pjangler registry; log = `toad` bank receipts) — same driver-over-machine pattern, one level higher.

---

## 8. Migration roadmap (Hermes-fleet → unified Momo/Toad)

1. **Freeze the SSOT** — `momo/skill/` (already diff-clean vs `33GOD/skills/momo`). Delete the stale `skillex/all-skills/momo` reference in BRAINDUMP (path doesn't exist). Wire PILLARS.md into the Momo spec (its table still shows "Momo spec/soul ⬜ pending").
2. **Promote the Lifecycle machine** (§7) into one versioned spec; per-repo labels via the `tp` map.
3. **Build the Hermes adapter** (momo E3/E5): Momo → SOUL/role renderer + copier shell-out; neutralize honcho. **Use the existing shared fanout** (`skillex/scripts/skill_ssot.py`, `all-skills/agent-config-fanout`) — **do NOT** lift Toad's fanout engine (see §9 correction).
4. **Pilot on one heartbeat repo** (slowburns or candystore): re-point its PM behavior to the Momo spec; run interactive Momo + the sentinel against a shared WIP=1 lock; verify no double-drive.
5. **Land the real coexistence lock** (momo E2/S2.3) before enabling any repo where a human also drives — the ~60s sentinel + interactive Momo on one board is a live TOCTOU. **Not deferrable.**
6. **Roll the remaining 21** via the adapter; while backfilling, fix drifted fields, repair the 2 failed checkpoints, prune debris. Drive off each unit's `HERMES_HOME`.
7. **Stand up Toad** above the fleet; give the `toad` bank its three mental models; close the pjangler lifecycle gap (`repo_ensure`/`repo_link`/`board_ensure`/composite `project_create`); retire `toad-mcp` → pjangler-mcp.
8. **End-state policy:** interactive Momo in every repo (any CLI) · autonomous Hermes carrier per-repo by choice · one WIP=1 lock/board · one Hindsight bank/repo · one cross-repo `toad` bank · one Lifecycle machine · one PILLARS.md referenced (never forked).

---

## 9. Corrections to stale docs/plans (trust disk, not docs)

- **Bloodbank identity scheme:** momo `record-decision.py` emits `source=urn:33god:agent:<name>:<repo>` — that string exists **nowhere** on disk. The real Hermes scheme is `producer=hermes-agent:<agent_id>`, `source=hermes://agent/<agent_id>`. The twins should emit the same scheme → fix in `record-decision.py`.
- **Toad fanout:** momo `epics.md` S4.2 / architecture §9 plan to "extract Toad's fanout engine," but Toad's approved 2026-07-15 correction **retires** that engine in favor of skillex/shared fanout. Following the momo docs would fork a dead engine.
- **`skillex/all-skills/momo`** (BRAINDUMP) — dead path; the skill is `33GOD/skills/momo` (already lifted to `momo/skill/`).
- **`_lib.sh:157`** RUNTIME_SCAFFOLD_DIR fallback `$HOME/code/hermes-agent-template/runtime-scaffold` is missing the `33GOD/` segment (broken; masked by the primary `$ROLE_DIR/.runtime-scaffold`).
- **`20-runtime-repo.sh`** has the PM Voxxy block **duplicated verbatim** (lines 147-165 & 167-185).
- **`agents-registry.yaml`** older entries point `hermes.bin/repo` at the pre-move `~/code/hermes-agent` (now `~/.hermes/hermes-agent`).
- **hermes-agent-template** standalone checkout (`576327e`) is a strict ancestor of the live submodule (`1c6482a` in `pjangler/templates/hermes-agent`) → **stale**; still carries the retired scrum-master generation. Canonical provisioner = `copier copy gh:delorenj/hermes-agent-template`.
