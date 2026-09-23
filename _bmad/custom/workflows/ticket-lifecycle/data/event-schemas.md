# Bloodbank Contract — ticket-lifecycle

This workflow publishes **no** ticket events. It moves tickets; the facts
follow on their own.

## The rule

Agents never emit `bloodbank.repo.task.*` or `bloodbank.repo.board.*`. Those
facts have exactly one producer: the Plane webhook, normalized by the n8n
`Plane → Bloodbank` workflow
(`~/code/33GOD/bloodbank/docs/plane-event-normalization.md`).

| What this workflow does | What the webhook normalizer publishes |
| --- | --- |
| moves the ticket to a new state | `bloodbank.repo.task.updated` (`provider_event_type: plane.ticket.transitioned`) |
| edits the ticket (title, description, AC, labels) | `bloodbank.repo.task.updated` (`provider_event_type: plane.ticket.updated`) |
| posts an audit comment | `bloodbank.repo.task.appended` (`provider_event_type: plane.ticket.commented`) |

So every transition this workflow drives — triage, refining, ready,
in_progress, review, qa, done, blocked — already becomes one
`bloodbank.repo.task.updated`, carrying the lossless Plane ticket. A second,
hand-written copy from the workflow would be a duplicate fact with a
different provenance, and consumers would count the transition twice.

## How to move a ticket

- Write the state change through **`px`** — the one Plane writer — using the
  state names in {workflowConfig}. Where a `px` verb is missing, use the
  ticket-provider adapter the repo already declares; never add an emit step to
  make up for it.
- Post the `[TICKET-LIFECYCLE]` audit comment on the ticket. The comment is the
  place for detail (rubric evidence, failure history, stuck-state durations);
  it reaches the bus as `bloodbank.repo.task.appended`.
- Then move on. Do not publish anything, do not wait for an echo, and do not
  call `bb emit` for a `repo.task.*` or `repo.board.*` type.

## Staleness

A state that exceeds its max duration in {workflowConfig} is not an event.
Move the ticket to `blocked` and put the detail in the audit comment:

```
[TICKET-LIFECYCLE] State Transition
---
from: {stuck state}
to: blocked
timestamp: {ISO 8601}
agent: orchestrator
reason: ticket-lifecycle-staleness
details:
  stuck_state: {state the ticket is stuck in}
  duration_minutes: {how long it has been in this state}
  max_duration_minutes: {configured max from workflow.yaml}
---
```

The move to `blocked` becomes `bloodbank.repo.task.updated`; the comment
becomes `bloodbank.repo.task.appended`. Consumers read the reason from there.

## What Momo may still publish

Judgment, not ticket state. A consequential call (pulling from To Do, cutting
scope, accepting a review) is recorded with the Momo skill's
`scripts/record-decision.py`, which publishes
`bloodbank.repo.decision.recorded`. That is a different fact from the ticket
move and is never a substitute for it.
