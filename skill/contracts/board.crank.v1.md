# board.crank.v1

The input, deployment receipt, worker observation and output receipt schemas are
[`board.crank.v1.json`](board.crank.v1.json). This is a control adapter for the
existing Momo per-ticket pipeline, supporting the deployed Hermes profile route.
It does not implement stateless contractors or certify their prerequisites.

Use Node 24.6 or newer, Python 3, and installed dependencies in the supplied
Bloodbank source root:

```sh
node skill/scripts/momo-board-crank.mjs inspect \
  --config /runtime/board-crank.json \
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank

node skill/scripts/momo-board-crank.mjs execute \
  --config /runtime/board-crank.json \
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank

node skill/scripts/momo-board-crank.mjs execute --replay \
  --config /runtime/board-crank.json \
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank

node skill/scripts/momo-board-crank.mjs reconcile \
  --config /runtime/board-crank.json \
  --pilot-root /source/pilot --bloodbank-root /source/bloodbank
```

`inspect` and `--dry-run` perform no lease, journal, bus or ticket writes.
`execute` selects at most one ticket, waits only for its matching started
lifecycle, and exits. It first attempts reconciliation of an active prior journal.
`reconcile` retires a proven completed fence without dispatch or ticket changes.
Exit 78 means refused/uncertain, 124 means the 45-second budget expired.
Busy and idle are normal exit-zero outcomes, distinguished in JSON.

## Deployment gate

No enabled configuration, deployment receipt, worker-status producer or cron is
shipped. Source tests cannot supply live prerequisites. The parent/runtime owner
must resolve 33GOD-44/46/50 and independently verify a single driver, gateway
command-ID/exact-envelope journal, deployed contractor/version, bundle digest,
board binding, profile, memory policy and independent review roles first.

The input explicitly names project/workspace/board/workdir; contractor/version in
`hermes-profile` mode; skill root/SHA256; memory `write_bank`/`recall_banks`; three
distinct implementer/spec-reviewer/quality-reviewer actors; runtime paths and
NATS hostname. No credentials belong in inputs or receipts. Pilot resolves its
normal configuration and credentials in memory.

The runtime owner authors the separate `board.crank.runtime.v1` receipt after
independent runtime acceptance. Matching binding, contractor, profile, shared
lease, journal directory, worker-status file, bundle digest, memory policy, roles,
`accepted`, `single_driver`, `gateway_command_journal`, `independent_reviews`,
`control_lease_handoff`, `verified_at` and `expires_at`
are checked on each pass. This is an acceptance attestation, not an automatic
installed-service audit. Fabricated/stale attestations are not deployment proof.

`skillDigest(skillRoot)` in `scripts/lib/board_crank_ports.mjs` computes SHA256 of
SKILL.md, delegation.md and board-clearing-loop.md joined with NUL. Changed bundles
need new acceptance; pending work binds the complete contractor and runtime
configuration, including receipt paths and broker, and refuses changes. Keep the
accepted per-board journal directory stable while any execution remains pending.

The same runtime owner produces `board.crank.workers.v1` from actual implementation
and review supervision: board, `observed_at` and every pending/active/review
execution (`ticket_id`, `command_id`, `status`). Empty means verified absence,
never a failed probe. Observations older than 60 seconds or from the future
refuse execution. The driver lease must be exactly the manifest-bound
`<role_dir>/runtime/wip-driver.lock`. The adapter uses `momo-wip-lock.py`, unique
owners, refresh and owner-safe release; it never uses `--steal`.

The gateway publishes started before handing the prompt to Hermes. The control
adapter still holds its short lease while it verifies start and patches state/date.
The PM must wait for that lease's release and acquire the SAME path with a unique
owner before driving implementation/review. The invocation supplies that path and
instruction. `control_lease_handoff` attests that this installed handoff was tested;
it is a runtime acceptance prerequisite, not proof supplied by the prompt itself.

Journal storage must already exist at its canonical path outside source or in an
already ignored runtime directory; symlink aliases are refused. Deployment/worker
receipts also belong outside source or in existing
ignored runtime storage. A NATS URL cannot contain credentials. There is no
source-side runtime setup or default enabled input.

## Readiness and selection

Only the unique exact `Todo` lane with `lifecycle:triaged` is considered. Tickets
need a title, enumerated/testable acceptance criteria and FR references. Drafts,
archives, deleted items, blocked/refining/needs-input labels, epic labels and
parents with children are excluded. Written unresolved prerequisites without
matching native dependencies are excluded.

Pilot's current Plane API supplies `work-items/<id>/relations/`. Every `blocked_by`,
`start_after` and `finish_after` predecessor must be known on this board and
completed; cancellation does not satisfy a dependency. Missing/unknown/cross-board
dependency truth excludes the candidate. Cycle-enabled boards must supply current
cycles/memberships; future/finished assignments are ineligible. Cycle-disabled
boards do not invent cycles. Rank urgent/high/medium/low/none, then active-cycle
fit, known downstream tickets unblocked, oldest creation time and stable ID.
Scores, rubric, rationale and exclusions persist in the journal.

Any exact In Progress ticket, agent:working ticket or fresh runtime execution
blocks new dispatch. Expired driver TTL never frees implementation WIP. A pass
caps Todo hydration at 100 items and has a 45-second watchdog; a larger or
unobservable board refuses rather than selecting from a partial sample.

## Dispatch and recovery

Bloodbank's canonical builder/validator construct its existing invocation command,
carrying contractor/version, project, board, ticket, workdir, memory policy,
roles and shared lease. Canonical `reason: ticket-delegation` is retained for
existing completion consumers; `origin` attributes the Board Cranker. The existing
delegation prompt is extended to preserve fields and leave
initial state/date writes to the adapter. The PM delegates product code; spec and
quality review require distinct fresh actors and the existing gates.

The exact envelope and digest are fsynced before publication. Bloodbank's publisher
connection seam uses its installed official JetStream client to require a
BLOODBANK_COMMANDS PubAck. Stable IDs and identical bytes reach the gateway's
command-ID/envelope-digest journal. There is no new bus subject or copied
envelope/wire/credential grammar.

PubAck is storage evidence. Started proof needs schema-valid turn.started caused
by the command and invocation.started caused by that turn. Command/idempotency,
correlation, target/profile, producer/service, thread/turn and full context must
match. Gateway starts precede actual Hermes handling: they acknowledge that
lifecycle, not proof that a delegated worker finished. Retained receipts are read
through Bloodbank direct-get helpers without creating a consumer.

After matching start, reload runtime, route, board and selected ticket. PATCH only
state and an absent start_date through Pilot editIssue. Preserve labels, assignees
and unrelated content. An immediate second ticket read refuses detected human
changes; journal the PATCH intent before sending and read back afterwards. Plane
does not supply an atomic conditional write here, so the final read/PATCH window
remains a concurrency limitation for independent review.

Publication failure or unmatched start leaves the ticket ready and retains
uncertainty. A normal pass checks receipts; explicit `--replay` sends only the
saved command after revalidation. No other worker can be minted while fenced.
After shared lease acquisition the adapter reloads the journal and decides from
that fresh value. A contender that observed no journal before waiting cannot
overwrite an intent persisted by the preceding driver.
Corrupt journals, changed pending configuration, missing/ineligible routes,
managed/shadow modes and unavailable prerequisites fail closed.

Lost PATCH responses are read back. Partial mutation, later human transitions and
missing readback remain truthful uncertainty. No PATCH or compensation is blindly
replayed. `mutation_conflict` needs the existing runtime owner's investigation.
There is no force-clear flag and no TTL expiry for an implementation fence.

## Completion reconciliation

The existing Momo runtime owner invokes reconciliation, explicitly or at the
start of a later execute pass, under the SAME driver lease. Only an active fence
can be retired, after all three agree:

1. A schema-valid invocation.completed matches the saved command, idempotency,
   target/profile, full context and exact started-event causation.
2. A worker observation at or after completion reports zero pending/active/review
   workers anywhere on this board and is no older than 60 seconds.
3. Fresh board/ticket reads show the original ticket in unique Done/completed,
   no other In Progress/agent:working WIP, unchanged route and binding.

Completion and original command/start/terminal/readback evidence are durably
archived in `completed/<command_id>.json`. The next pass can dispatch at most one
later ticket. A crash between completion persistence and archive creation is
recoverable: reconciliation repairs the archive, and execute confirms it before
replacing the completed journal. Archive failure prevents advancing a later ticket.
Inspect cannot retire a fence. PM completion alone, board state
alone, an empty snapshot alone, TTL, failure events and ambiguous mutation phases
never retire it. The post-completion worker-status producer and retained gateway
receipts are explicit runtime prerequisites; this change enables neither.

All output receipts carry `live_execution_proof: false`. Installed runtime/cron,
real broker receipts, worker evidence and independent review remain separate
parent acceptance work.
