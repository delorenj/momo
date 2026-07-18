from __future__ import annotations

import copy
import importlib.util
import json
import uuid
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "skill" / "scripts" / "lifecycle_client.py"
SPEC = importlib.util.spec_from_file_location("momo_lifecycle_client", MODULE_PATH)
assert SPEC and SPEC.loader
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)

LIFECYCLE_ID = "11111111-1111-4111-8111-111111111111"
CORRELATION_ID = "22222222-2222-4222-8222-222222222222"
CAUSATION_ID = "33333333-3333-4333-8333-333333333333"
NOW = "2026-07-18T12:00:00Z"
ACTOR = {"type": "agent_cli", "agent_id": "momo", "cli": "codex", "provider": "openai"}


def test_obligation_invocation_resolves_canonical_skill_and_is_stable():
    snapshot = projection()
    first = client.build_obligation_invocation(
        snapshot,
        actor=ACTOR,
        target_agent_id="reviewer-1",
        requested_at=NOW,
        correlation_id=CORRELATION_ID,
        causation_id=CAUSATION_ID,
        rationale={"basis": ["evidence-over-status"], "why": "review is due"},
    )
    second = client.build_obligation_invocation(
        snapshot,
        actor=ACTOR,
        target_agent_id="reviewer-1",
        requested_at=NOW,
        correlation_id=CORRELATION_ID,
        causation_id=CAUSATION_ID,
    )

    command = first["invocation_command"]
    assert command["id"] == second["invocation_command"]["id"]
    assert command["command_id"] == second["invocation_command"]["command_id"]
    assert command["subject"] == "bloodbank.cmd.v1.agent.invocation.start"
    assert command["delivery"] == "single_consumer"
    assert command["correlationid"] == CORRELATION_ID
    assert command["causationid"] == CAUSATION_ID
    assert command["data"]["context"]["skill_ref"] == {
        "name": "bmad-code-review",
        "selector": "6.10.2",
    }
    assert command["data"]["context"]["evidence_completion"] == {
        "lifecycle_id": LIFECYCLE_ID,
        "obligation_id": "independent-review",
        "obligation_satisfied": True,
    }
    assert first["decision_rationale"]["why"] == "review is due"
    assert "decision_rationale" not in command["data"]


def test_non_pending_or_illegal_work_is_never_invoked():
    snapshot = projection()
    snapshot["obligations"][0]["status"] = "satisfied"
    with pytest.raises(client.LifecycleClientError, match="no matching"):
        client.build_obligation_invocation(
            snapshot,
            actor=ACTOR,
            target_agent_id="reviewer-1",
            requested_at=NOW,
            correlation_id=CORRELATION_ID,
            causation_id=CAUSATION_ID,
        )

    snapshot = projection()
    snapshot["legal_frontier"][0]["allowed"] = False
    with pytest.raises(client.LifecycleClientError, match="no legal current work"):
        client.build_obligation_invocation(
            snapshot,
            actor=ACTOR,
            target_agent_id="reviewer-1",
            requested_at=NOW,
            correlation_id=CORRELATION_ID,
            causation_id=CAUSATION_ID,
        )


def test_lifecycle_command_has_locked_context_and_separate_rationale():
    plan = client.build_lifecycle_intent(
        projection(obligations=[]),
        actor=ACTOR,
        capability_version=1,
        requested_at=NOW,
        correlation_id=CORRELATION_ID,
        causation_id=CAUSATION_ID,
        evidence={"event_id": "77777777-7777-4777-8777-777777777777", "result": "pass"},
        rationale={"basis": ["one-source-of-truth"], "why": "authority says legal"},
    )
    command = plan["lifecycle_command"]
    assert command["subject"] == "bloodbank.cmd.v1.lifecycle.intent.submit"
    assert command["actor"] == ACTOR
    assert uuid.UUID(command["command_id"])
    assert command["idempotency_key"].endswith("state:7")
    assert command["correlationid"] == CORRELATION_ID
    assert command["causationid"] == CAUSATION_ID
    assert command["data"]["expected_state_version"] == 7
    assert command["data"]["intent"] == {
        "name": "transition",
        "target": "active",
        "parameters": {
            "selected_frontier_id": "transition:planned:active",
            "evidence": {
                "event_id": "77777777-7777-4777-8777-777777777777",
                "result": "pass",
            },
        },
    }
    assert command["data"]["capability"] == {
        "capability_id": "momo-grant",
        "capability_version": 1,
        "action": "lifecycle.intent.submit",
        "scope": f"lifecycle:{LIFECYCLE_ID}",
        "issued_to": "momo",
    }
    assert plan["decision_rationale"]["why"] == "authority says legal"
    assert "decision_rationale" not in json.dumps(command)


def test_stale_version_illegal_frontier_and_missing_capability_fail_closed():
    stale = projection(obligations=[])
    stale["projection_status"] = "stale"
    with pytest.raises(client.LifecycleClientError, match="not current"):
        build_intent(stale)

    wrong_version = projection(obligations=[])
    wrong_version["legal_frontier"][0]["expected_state_version"] = 6
    with pytest.raises(client.LifecycleClientError, match="no matching allowed"):
        build_intent(wrong_version)

    missing_grant = projection(obligations=[])
    missing_grant["capabilities"] = []
    with pytest.raises(client.LifecycleClientError, match="no current authoritative"):
        build_intent(missing_grant)


def test_invalid_skill_reference_is_not_resolved():
    snapshot = projection()
    snapshot["obligations"][0]["skill_ref"] = {
        "name": "../../direct-writer",
        "selector": "latest version",
    }
    with pytest.raises(client.LifecycleClientError, match="canonical skill name"):
        client.pending_obligations(snapshot)


def test_verdict_gate_matches_every_stable_command_identity():
    command = build_intent(projection(obligations=[]))["lifecycle_command"]
    reply = authoritative_reply(command, verdict="applied")
    result = client.verify_command_verdict(command, reply)
    assert result["verdict"] == "applied"

    stale = authoritative_reply(command, verdict="stale")
    with pytest.raises(client.LifecycleClientError, match="not applied"):
        client.verify_command_verdict(command, stale)

    mismatch = authoritative_reply(command, verdict="applied")
    mismatch["data"]["command_id"] = str(uuid.uuid4())
    with pytest.raises(client.LifecycleClientError, match="command_id"):
        client.verify_command_verdict(command, mismatch)


def test_publish_uses_only_canonical_bloodbank_subject():
    command = build_intent(projection(obligations=[]))["lifecycle_command"]
    calls = []

    def publish(subject, body, **kwargs):
        calls.append((subject, json.loads(body), kwargs))

    assert client.publish_envelope(command, publish=publish) == command["subject"]
    assert calls == [
        (
            "bloodbank.cmd.v1.lifecycle.intent.submit",
            command,
            {"client_name": "momo-lifecycle-client"},
        )
    ]

    invalid = copy.deepcopy(command)
    invalid["subject"] = "provider.direct.write"
    with pytest.raises(client.LifecycleClientError, match="non-canonical"):
        client.publish_envelope(invalid, publish=publish)


def test_client_has_no_direct_mutation_transport_or_local_truth_store():
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert 'method="GET"' in source
    for forbidden in (
        'method="POST"',
        'method="PUT"',
        'method="PATCH"',
        "psycopg",
        "sqlite",
        "trello",
        "plane",
        "lifecycle_state =",
    ):
        assert forbidden not in source


def build_intent(snapshot):
    return client.build_lifecycle_intent(
        snapshot,
        actor=ACTOR,
        capability_version=1,
        requested_at=NOW,
        correlation_id=CORRELATION_ID,
        causation_id=CAUSATION_ID,
        evidence={"event_id": "77777777-7777-4777-8777-777777777777"},
    )


def projection(*, obligations=None):
    if obligations is None:
        obligations = [
            {
                "id": "independent-review",
                "kind": "independent_review",
                "status": "pending",
                "description": "Obtain independent review.",
                "skill_ref": {"name": "bmad-code-review", "selector": "6.10.2"},
                "owner_id": None,
                "due_at": None,
                "source_observation_ids": [],
            }
        ]
    return {
        "lifecycle_id": LIFECYCLE_ID,
        "repo": "delorenj/33GOD",
        "projection_status": "current",
        "state_version": 7,
        "legal_frontier": [
            {
                "id": "transition:planned:active",
                "kind": "state_transition",
                "action": "transition",
                "allowed": True,
                "capability_required": "lifecycle.intent.submit",
                "reason_code": "LEGAL_TRANSITION",
                "expected_state_version": 7,
            }
        ],
        "obligations": obligations,
        "capabilities": [
            {
                "capability_id": "momo-grant",
                "actor_id": "momo",
                "actions": ["lifecycle.intent.submit"],
                "scope": f"lifecycle:{LIFECYCLE_ID}",
                "issued_at": "2026-07-18T11:00:00Z",
                "expires_at": None,
                "state_version": 7,
            }
        ],
        "source": {"event_id": CAUSATION_ID},
    }


def authoritative_reply(command, *, verdict):
    data = command["data"]
    applied = verdict in {"applied", "idempotent"}
    return {
        "subject": "bloodbank.rpy.v1.lifecycle.intent.submit",
        "data": {
            "reply_to_command_event_id": command["id"],
            "command_id": command["command_id"],
            "idempotency_key": command["idempotency_key"],
            "lifecycle_id": data["lifecycle_id"],
            "expected_state_version": data["expected_state_version"],
            "observed_state_version": data["expected_state_version"],
            "verdict": verdict,
            "mutated": verdict == "applied",
            "resulting_state_version": data["expected_state_version"] + 1 if applied else None,
            "applied_event_id": str(uuid.uuid4()) if applied else None,
        },
    }
