# Momo - Development Guide

**Date:** 2026-07-16

This guide covers how the repo is wired **today** (tooling, secrets, versioning, planning
workflow) and the known scaffold gaps to close before/while implementation begins. There is
no product code yet, so there is nothing to build, run, or test — this is a **planning &
scaffold** guide.

## Prerequisites

| Tool | Why | Notes |
|---|---|---|
| [`mise`](https://mise.jdx.dev) | task runner, env, tool versions | Drives everything via `mise.toml` |
| [`op` (1Password CLI)](https://developer.1password.com/docs/cli/) | secrets | `op inject` materializes `.env` on enter |
| `git` | versioning | version is derived from **git tags** |
| BMAD Method v6.10.1 | planning/doc workflows | installed under `_bmad/` |
| Plane access (workspace `33god`) | ticket board | project identifier `MOMO` |

## Environment Setup

```bash
cd /home/delorenj/code/33GOD/momo
mise trust           # trust this repo's mise config
mise install         # install pinned tools
mise ls              # verify
```

On `mise enter`, the `[hooks].enter` block runs (see `mise.toml`):

1. `.mise/scripts/link-agentfiles.sh` — symlink `AGENTS.md` → `CLAUDE.md` / `GEMINI.md`.
2. `op inject -i .env.op > .env` — materialize secrets from 1Password.
3. `.mise/scripts/codegraph.sh` — start/refresh the codegraph index daemon.

> ⚠️ Steps 1 and 3 currently **do not behave as intended** — see
> [Known scaffold gaps](#known-scaffold-gaps).

### Secrets

- Secrets are **never committed.** `.env` is gitignored; `.env.op` (committed) holds only
  1Password references (e.g. `OPENROUTER_API_KEY=op://DeLoSecrets/openrouter/OpenCode`).
- Regenerate `.env` any time with: `op inject -i .env.op > .env`.
- Provision the shared project Hindsight key: `mise run hindsight-setup`
  *(note: the backing script is currently missing — see gaps).*

## Versioning

Versioning is managed by the **mise-versioning** skill (managed block in `mise.toml`,
manifest `.mise/version-files.conf`). The only version source is **git tags** (`gittag .`)
— there are no manifest files to keep in sync yet.

```bash
mise run version            # print current version (vX.Y.Z from git tags)
mise run version:bump       # bump patch (alias: version:bump-patch)
mise run version:bump-minor # bump minor
mise run version:bump-major # bump major
mise run version:check      # verify parity across versioned files
mise run version:sync       # force all versioned files to highest version
```

> No git tags exist yet, so `version` will report the tool's zero/base version until the
> first tag is cut. When product code (and manifests) land, add them to
> `.mise/version-files.conf` so `--version` never lies after a bump.

## Planning Workflow (BMAD)

Planning/documentation runs through **BMAD v6.10.1**, installed as skills. Because this
install compiles workflows to skills, invoke them via the **Skill tool / slash commands**,
not the legacy `_bmad/**/workflow.xml` paths (which don't exist in v6.10.x).

- `/bmad-bmm-document-project` → the `bmad-document-project` skill (**produced this `docs/`**).
- Planning artifacts output to `_bmad-output/planning-artifacts/`.
- Implementation artifacts output to `_bmad-output/implementation-artifacts/`.
- Project knowledge (this docs set) lives in `docs/` per `_bmad/bmm/config.yaml`.

Suggested next BMAD steps once you're ready to build: product brief → PRD → architecture
→ epics/stories (see [architecture.md §10](./architecture.md#10-the-gap--what-build-momo-entails)).

## Ticket Board

- Identity in `.project.json`: provider `plane`, workspace `33god`, identifier `MOMO`,
  `board_id` empty, `state: planned`, reconcile automation disabled.
- Momo resolves project/provider projection identity from this file. Target
  state-changing intent goes through Lifecycle; the current `tp` adapter is a
  legacy/projection path rather than lifecycle authority.

## Code Intelligence (codegraph)

- The repo is indexed: `.codegraph/codegraph.db` (~6 MB) with a running daemon
  (`.codegraph/daemon.pid`, `daemon.sock`).
- Query it once product code exists via the `codegraph` MCP tools (search, callers,
  callees, impact, explore).

## Known scaffold gaps

These are real inconsistencies found during the scan — safe to fix as part of hardening
the scaffold:

1. **`.mise/scripts/codegraph.sh` is missing** but referenced by `mise.toml`
   `[hooks].enter`. The codegraph daemon is running (provisioned by other means), so the
   enter-hook line currently errors/no-ops. → Add the script, or remove the hook line.
2. **`.mise/scripts/hindsight-setup.sh` is missing** but referenced by the
   `hindsight-setup` task. → `mise run hindsight-setup` will fail until the script exists.
3. **`AGENTS.md` does not exist**, so `link-agentfiles.sh` no-ops: no `CLAUDE.md` /
   `GEMINI.md` symlinks are created, and the `[[watch_files]]` watcher on `AGENTS.md` never
   fires. → Author `AGENTS.md` (the canonical agent-instructions file) to activate this.
4. **`agents/hermes/pm` is on `mise` `_.path`** but the `agents/` directory does not exist.
   → Create it when the Hermes PM/agent files are added, or trim the path entry.
5. **No product code, manifests, or lockfiles** — expected (pre-implementation), noted so
   the absence isn't mistaken for a broken checkout.

## Contributing

- **Doctrine is referenced, not forked.** [`PILLARS.md`](../PILLARS.md) is the single source
  of truth; agent souls/specs must *link* to it (see its wiring checklist), never copy it.
- **Managed blocks** (e.g. `# >>> mise-versioning >>>` in `mise.toml`) are regenerated by
  their skills — do not hand-edit; re-run the skill's init instead.
- **`.copier-answers.yml`** is copier-owned — never edit manually (it's overwritten on
  template updates).

---

_Generated using BMAD Method `document-project` workflow_
