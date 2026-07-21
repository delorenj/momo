# Render map — role.yaml + SOUL.md  <-  Momo spec / copier identity

Sources: `S` = Momo spec (`momo-agent.spec.yaml`), `I` = copier identity var,
`P` = pipeline post-gen script (`.scripts/*`), `C` = constant/template default.

## role.yaml (`template/role.yaml.jinja`)

| target field | src | value |
| --- | --- | --- |
| `repo` | I | `target_repo` |
| `role` | I | `role` |
| `agent_id` | I | `{target_repo}-{role}` |
| `display_name` | I | `display_name` |
| `purpose` | S | `roles.<role>.purpose_template.format(repo=target_repo)` |
| `model.provider` / `model.name` | I | `model_provider` / `model_name` (empty = inherit) |
| `profile` | I | `agent_id` |
| `telegram.bot_username` | I | `bot_handle` |
| `ticket_provider.name` | I | `ticket_provider` |
| `ticket_provider.board_id` / `board_url` | P | `42-ticket-provider.sh` |
| `ticket_provider.workspace` / `project` | I+P | `plane_workspace` + `42-ticket-provider.sh` |
| `ticket_provider.in_review` / `completed` | S | `lifecycle_pointer.per_repo_state_map` `states:` overrides (non-standard boards only) |
| `reconcile.enabled` | S | `roles.<role>.behavior.reconcile.enabled` |
| `reconcile.grace_hours` | S | `roles.<role>.behavior.reconcile.grace_hours` |
| `reconcile.auto_review` | S | `roles.<role>.behavior.reconcile.auto_review` |
| `plane.workspace` / `identifier` | I+P | `plane_workspace` + `42-ticket-provider.sh` |
| `bloodbank.subscribe[]` | C | template default subjects (`bloodbank.evt.v1.repo.>`, `bloodbank.cmd.v1.agent.>`) |
| `bloodbank.routing.repo` | I | `target_repo` |
| `bloodbank.routing.target_agent_id` | I | `agent_id` |
| `bloodbank.producer` | I | `hermes-agent:{agent_id}` **(canonical producer scheme record-decision must match)** |
| `runtime.github_owner` | I | `runtime_repo_owner` |
| `runtime.github_repo` | I | `runtime_repo` (`agent-hm-{repo}-{role}`) |
| `runtime.submodule_path` | C | `./runtime` |
| `runtime.checkpoint.cadence` / `on_session_end` | C/S | template default (`heartbeat` / true) |
| `provisioned_at` / `provisioned_by` | C | template provenance |

## SOUL.md (`template/SOUL.md.jinja`)

| target section/field | src | value |
| --- | --- | --- |
| H1 + `display_name`, `target_repo` | I | identity |
| Identity table (agent_id, repo, role, telegram, purpose) | I + S(purpose) | identity; purpose from `roles.<role>.purpose_template` |
| Scope (runtime submodule, `runtime_repo_owner`/`runtime_repo`) | I | identity |
| **Tone** | S | `personality.tones[soul_tone]` (selected by I `soul_tone`) — moved from jinja hardcode to spec |
| Default contract: envelope `type` pattern | C | constant CloudEvents rule |
| Default contract: `actor.agent_id` | I | `agent_id` |
| Default contract: `producer` | I | `hermes-agent:{agent_id}` |
| Default contract: `source` | I | `hermes://agent/{agent_id}` **(canonical source scheme record-decision must match)** |
| **Role-specific behavior** | S | `roles.<role>.charter` + `prime_directives` + `default_execution` + `bloodbank_events` — moved from jinja hardcode to spec |
| DeloNet conventions | C | constant doctrine (paths, subnet 192.168.1.0/24, hostnames, Plane refs) |
| **Memory hygiene** | S | `memory.hygiene.format(repo_slug=slug)` — **replaces** the `runtime/memories/` text; points at Hindsight bank `{repo_slug}` |

### Template change required (small PR to hermes-agent-template)

Three SOUL.md.jinja sections are currently hardcoded prose; to make them
spec-driven, add copier vars and swap the literals for them:

- `soul_tone` block  ->  `{{ soul_tone_text }}`
- Role-specific behavior block  ->  `{{ soul_role_behavior }}` + `{{ soul_bloodbank_events }}`
- Memory hygiene block  ->  `{{ soul_memory_hygiene }}`

Until that PR lands, the adapter applies these three as a post-render SOUL.md
rewrite (step 3c in `render_agent.py`) so no template change blocks rollout.

## Not from the spec (identity-only, per repo)

`target_repo, role, agent_id, display_name, bot_handle, runtime_repo,
runtime_repo_owner, profile, ticket_provider, plane_workspace, model_provider,
model_name, soul_tone` — all copier answers. The adapter derives two more:
`repo_slug` (= Hindsight bank, worktree-safe) and `momo_agent_id` (`{repo_slug}-momo`).
