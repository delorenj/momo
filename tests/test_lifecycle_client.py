from __future__ import annotations

import copy
import importlib.util
import json
import uuid
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

MODULE_PATH = Path(__file__).resolve().parents[1] / "skill" / "scripts" / "lifecycle_client.py"
SPEC = importlib.util.spec_from_file_location("momo_lifecycle_client", MODULE_PATH)
assert SPEC and SPEC.loader
client = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client)

BLOODBANK_ROOT = Path(__file__).resolve().parents[2] / "bloodbank"
SCHEMAS_ROOT = BLOODBANK_ROOT / "schemas"
LIFECYCLE_ID = "11111111-1111-4111-8111-111111111111"
SNAPSHOT_EVENT_ID = "33333333-3333-4333-8333-333333333333"
NOW = "2026-07-18T12:00:00Z"
ACTOR = {"type": "agent_cli", "agent_id": "momo", "cli": "codex", "provider": "openai"}
EVIDENCE = {
    "kind": "skill_completion",
    "outcome": "completed",
    "artifact_id": "review-report:42",
    "artifact_sha256": "a" * 64,
    "summary": "Independent review completed with no material findings.",
}
SCHEMA_BY_REF = {
    "bloodbank.v1.agent.invocation.start.v1": ("bloodbank/v1/agent/invocation.start.v1.json"),
    "bloodbank.v1.lifecycle.intent.submit.command.v1": (
        "bloodbank/v1/lifecycle/intent.submit.command.v1.json"
    ),
    "bloodbank.v1.lifecycle.intent.submit.reply.v1": (
        "bloodbank/v1/lifecycle/intent.submit.reply.v1.json"
    ),
    "bloodbank.v1.lifecycle.obligation_evidence.submitted.v1": (
        "bloodbank/v1/lifecycle/obligation_evidence.submitted.v1.json"
    ),
}


def test_pending_obligation_is_direct_actor_work_not_unrelated_frontier_authority():
    snapshot = projection()
    snapshot["legal_frontier"][0]["allowed"] = False

    plan = client.build_obligation_invocation(
        snapshot,
        actor=ACTOR,
        rationale={"why": "independent review is the authority obligation"},
        parameters={"review_depth": "adversarial"},
    )
    command = plan["invocation_command"]
    context = command["data"]["context"]

    assert command["data"]["target_agent_id"] == "agent:independent-reviewer"
    assert context["skill_ref"] == {"name": "bmad-code-review", "selector": "6.10.2"}
    assert context["parameters"] == {"review_depth": "adversarial"}
    assert context["completion_evidence_contract"] == {
        "type": "bloodbank.v1.lifecycle.obligation_evidence.submitted",
        "subject": "bloodbank.evt.v1.lifecycle.obligation_evidence.submitted",
        "obligation_id": "independent-review",
        "obligation_kind": "independent_review",
        "target_actor_id": "agent:independent-reviewer",
        "invocation_id": command["id"],
    }
    assert "authority_frontier" not in json.dumps(plan)
    assert "obligation_satisfied" not in json.dumps(plan)
    assert plan["decision_rationale"]["why"].startswith("independent")
    assert "decision_rationale" not in json.dumps(command)
    validate_with_bloodbank(command)


def test_invocation_semantic_identity_is_exact_and_retry_stable():
    first = client.build_obligation_invocation(
        projection(), actor=ACTOR, parameters={"review_depth": "adversarial"}
    )["invocation_command"]
    retry = client.build_obligation_invocation(
        projection(), actor=ACTOR, parameters={"review_depth": "adversarial"}
    )["invocation_command"]
    assert retry == first

    identity_fields = ("id", "command_id", "correlationid", "causationid", "idempotency_key")
    variants = []
    changed_parameters = projection()
    variants.append(
        client.build_obligation_invocation(
            changed_parameters, actor=ACTOR, parameters={"review_depth": "focused"}
        )["invocation_command"]
    )
    changed_obligation = projection()
    changed_obligation["obligations"][0]["description"] = "Review the final evidence packet."
    variants.append(
        client.build_obligation_invocation(
            changed_obligation, actor=ACTOR, parameters={"review_depth": "adversarial"}
        )["invocation_command"]
    )
    changed_owner = projection()
    changed_owner["obligations"][0]["owner_id"] = "agent:security-reviewer"
    variants.append(
        client.build_obligation_invocation(
            changed_owner, actor=ACTOR, parameters={"review_depth": "adversarial"}
        )["invocation_command"]
    )
    for variant in variants:
        assert all(variant[field] != first[field] for field in identity_fields)
        validate_with_bloodbank(variant)


def test_non_pending_missing_owner_and_invalid_skill_are_never_invoked():
    satisfied = projection()
    satisfied["obligations"][0]["status"] = "satisfied"
    with pytest.raises(client.LifecycleClientError, match="no matching"):
        client.build_obligation_invocation(satisfied, actor=ACTOR)

    missing_owner = projection()
    missing_owner["obligations"][0]["owner_id"] = None
    with pytest.raises(client.LifecycleClientError, match="owner_id"):
        client.build_obligation_invocation(missing_owner, actor=ACTOR)

    invalid_skill = projection()
    invalid_skill["obligations"][0]["skill_ref"] = {
        "name": "../../direct-writer",
        "selector": "latest version",
    }
    with pytest.raises(client.LifecycleClientError, match="canonical skill name"):
        client.build_obligation_invocation(invalid_skill, actor=ACTOR)


def test_completion_is_distinct_schema_exact_evidence_and_retry_stable():
    invocation = client.build_obligation_invocation(projection(), actor=ACTOR)
    first = client.build_obligation_completion_evidence(
        invocation, completed_at="2026-07-18T12:30:00Z", evidence=EVIDENCE
    )["completion_evidence"]
    retry = client.build_obligation_completion_evidence(
        invocation, completed_at="2026-07-18T12:30:00Z", evidence=EVIDENCE
    )["completion_evidence"]

    assert retry == first
    assert first["source"] == "urn:33god:service:momo"
    assert first["causationid"] == invocation["invocation_command"]["id"]
    assert first["correlationid"] == invocation["invocation_command"]["correlationid"]
    assert first["ordering_key"] == f"lifecycle:{LIFECYCLE_ID}"
    assert first["data"]["obligation_id"] == "independent-review"
    assert first["data"]["target_actor_id"] == "agent:independent-reviewer"
    assert first["data"]["evidence"] == EVIDENCE
    validate_with_bloodbank(first)

    changed_evidence = {**EVIDENCE, "artifact_sha256": "b" * 64}
    changed = client.build_obligation_completion_evidence(
        invocation, completed_at="2026-07-18T12:30:00Z", evidence=changed_evidence
    )["completion_evidence"]
    assert changed["id"] != first["id"]
    validate_with_bloodbank(changed)


@pytest.mark.parametrize(
    "evidence,match",
    [
        ({**EVIDENCE, "outcome": "requested"}, "completed skill work"),
        ({**EVIDENCE, "artifact_sha256": "ABC"}, "64 lowercase"),
        ({**EVIDENCE, "satisfied": True}, "canonical fields"),
    ],
)
def test_invocation_or_claims_cannot_stand_in_for_completion(evidence, match):
    invocation = client.build_obligation_invocation(projection(), actor=ACTOR)
    with pytest.raises(client.LifecycleClientError, match=match):
        client.build_obligation_completion_evidence(
            invocation,
            completed_at="2026-07-18T12:30:00Z",
            evidence=evidence,
        )


def test_lifecycle_command_derives_capability_version_and_is_schema_exact():
    plan = build_intent(projection(obligations=[]), rationale={"why": "authority says legal"})
    command = plan["lifecycle_command"]

    assert command["data"]["capability"] == {
        "capability_id": "momo-grant",
        "capability_version": 7,
        "action": "lifecycle.intent.submit",
        "scope": f"lifecycle:{LIFECYCLE_ID}",
        "issued_to": "momo",
    }
    assert command["data"]["requested_at"] == NOW
    assert command["time"] == NOW
    assert command["data"]["expected_state_version"] == 7
    assert plan["decision_rationale"]["why"] == "authority says legal"
    assert "decision_rationale" not in json.dumps(command)
    validate_with_bloodbank(command)


def test_lifecycle_semantic_identity_covers_every_material_request_field():
    first = build_intent(
        projection(obligations=[]),
        parameters={"mode": "strict"},
        evidence={"artifact_id": "review:1", "result": "pass"},
    )["lifecycle_command"]
    retry = build_intent(
        projection(obligations=[]),
        parameters={"mode": "strict"},
        evidence={"artifact_id": "review:1", "result": "pass"},
    )["lifecycle_command"]
    assert retry == first

    changed_evidence = build_intent(
        projection(obligations=[]),
        parameters={"mode": "strict"},
        evidence={"artifact_id": "review:2", "result": "pass"},
    )["lifecycle_command"]
    changed_parameters = build_intent(
        projection(obligations=[]),
        parameters={"mode": "normal"},
        evidence={"artifact_id": "review:1", "result": "pass"},
    )["lifecycle_command"]
    changed_capability_projection = projection(obligations=[])
    changed_capability_projection["capabilities"][0]["capability_version"] = 8
    changed_capability = build_intent(
        changed_capability_projection,
        parameters={"mode": "strict"},
        evidence={"artifact_id": "review:1", "result": "pass"},
    )["lifecycle_command"]
    identity_fields = ("id", "command_id", "correlationid", "causationid", "idempotency_key")
    for variant in (changed_evidence, changed_parameters, changed_capability):
        assert all(variant[field] != first[field] for field in identity_fields)
        validate_with_bloodbank(variant)


def test_stale_illegal_wrong_frontier_and_missing_capability_version_fail_closed():
    stale = projection(obligations=[])
    stale["projection_status"] = "stale"
    with pytest.raises(client.LifecycleClientError, match="not current"):
        build_intent(stale)

    illegal = projection(obligations=[])
    illegal["legal_frontier"][0]["allowed"] = False
    with pytest.raises(client.LifecycleClientError, match="no matching allowed"):
        build_intent(illegal)

    wrong_version = projection(obligations=[])
    wrong_version["legal_frontier"][0]["expected_state_version"] = 6
    with pytest.raises(client.LifecycleClientError, match="no matching allowed"):
        build_intent(wrong_version)

    wrong_frontier = projection(obligations=[])
    with pytest.raises(client.LifecycleClientError, match="no matching allowed"):
        build_intent(wrong_frontier, frontier_id="transition:waiting:active")

    missing_grant = projection(obligations=[])
    missing_grant["capabilities"] = []
    with pytest.raises(client.LifecycleClientError, match="no current authoritative"):
        build_intent(missing_grant)

    missing_version = projection(obligations=[])
    del missing_version["capabilities"][0]["capability_version"]
    with pytest.raises(client.LifecycleClientError, match="authoritative capability_version"):
        build_intent(missing_version)


def test_verdict_accepts_only_complete_matching_authority_reply():
    command = build_intent(projection(obligations=[]))["lifecycle_command"]
    reply = authoritative_reply(command, verdict="applied")
    validate_with_bloodbank(reply)
    result = client.verify_command_verdict(command, reply)
    assert result["verdict"] == "applied"

    idempotent = authoritative_reply(command, verdict="idempotent")
    validate_with_bloodbank(idempotent)
    assert client.verify_command_verdict(command, idempotent)["verdict"] == "idempotent"


@pytest.mark.parametrize(
    "path,value,match",
    [
        (("source",), "urn:33god:service:not-lifecycle", "source"),
        (("producer",), "momo", "producer"),
        (("service",), "other", "service"),
        (("subject",), "bloodbank.rpy.v1.lifecycle.status.updated", "subject"),
        (("type",), "bloodbank.v1.lifecycle.status.updated", "type"),
        (("kind",), "event", "kind"),
        (("domain",), "agent", "domain"),
        (("correlationid",), str(uuid.uuid4()), "correlationid"),
        (("causationid",), str(uuid.uuid4()), "causationid"),
        (("actor", "agent_id"), "momo", "actor"),
        (("data", "lifecycle_id"), "wrong", "lifecycle_id"),
        (("data", "repo"), "wrong/repo", "repo"),
        (("data", "command_id"), str(uuid.uuid4()), "command_id"),
        (("data", "capability_id"), "other-grant", "capability_id"),
        (("data", "responded_at"), "2026-07-18T12:00:01Z", "responded_at"),
    ],
)
def test_matching_looking_non_authority_or_identity_mismatch_reply_is_rejected(path, value, match):
    command = build_intent(projection(obligations=[]))["lifecycle_command"]
    reply = authoritative_reply(command, verdict="applied")
    target = reply
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(client.LifecycleClientError, match=match):
        client.verify_command_verdict(command, reply)


def test_rejection_verdict_is_verified_then_rejected_without_acceptance():
    command = build_intent(projection(obligations=[]))["lifecycle_command"]
    reply = authoritative_reply(command, verdict="stale")
    validate_with_bloodbank(reply)
    with pytest.raises(client.LifecycleClientError, match="not applied: stale"):
        client.verify_command_verdict(command, reply)


def test_publish_supports_only_exact_canonical_bloodbank_envelopes():
    command = build_intent(projection(obligations=[]))["lifecycle_command"]
    invocation_plan = client.build_obligation_invocation(projection(), actor=ACTOR)
    invocation = invocation_plan["invocation_command"]
    completion = client.build_obligation_completion_evidence(
        invocation_plan, completed_at="2026-07-18T12:30:00Z", evidence=EVIDENCE
    )["completion_evidence"]
    calls = []

    def publish(subject, body, **kwargs):
        calls.append((subject, json.loads(body), kwargs))

    for envelope in (command, invocation, completion):
        validate_with_bloodbank(envelope)
        assert client.publish_envelope(envelope, publish=publish) == envelope["subject"]
    assert [call[0] for call in calls] == [
        "bloodbank.cmd.v1.lifecycle.intent.submit",
        "bloodbank.cmd.v1.agent.invocation.start",
        "bloodbank.evt.v1.lifecycle.obligation_evidence.submitted",
    ]
    assert all(call[2] == {"client_name": "momo-lifecycle-client"} for call in calls)

    invalid = copy.deepcopy(command)
    invalid["subject"] = "provider.direct.write"
    with pytest.raises(client.LifecycleClientError, match="non-canonical"):
        client.publish_envelope(invalid, publish=publish)


def test_exact_local_schema_validation_detects_required_const_subject_and_version_drift():
    command = build_intent(projection(obligations=[]))["lifecycle_command"]
    mutations = [
        lambda value: value.pop("command_id"),
        lambda value: value.__setitem__("kind", "event"),
        lambda value: value.__setitem__("subject", "bloodbank.cmd.v1.lifecycle.status.update"),
        lambda value: value["data"].__setitem__("contract_version", 2),
    ]
    for mutate in mutations:
        invalid = copy.deepcopy(command)
        mutate(invalid)
        with pytest.raises(ValidationError):
            validate_with_bloodbank(invalid)


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
        "capability_version=1",
        "obligation_satisfied",
        "authority_frontier_basis",
    ):
        assert forbidden not in source


def build_intent(
    snapshot,
    *,
    frontier_id=None,
    rationale=None,
    parameters=None,
    evidence=None,
):
    return client.build_lifecycle_intent(
        snapshot,
        actor=ACTOR,
        frontier_id=frontier_id,
        rationale=rationale,
        parameters=parameters,
        evidence=evidence or {"artifact_id": "review:1", "result": "pass"},
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
                "owner_id": "agent:independent-reviewer",
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
                "capability_version": 7,
                "actor_id": "momo",
                "actions": ["lifecycle.intent.submit"],
                "scope": f"lifecycle:{LIFECYCLE_ID}",
                "issued_at": "2026-07-18T11:00:00Z",
                "expires_at": None,
                "state_version": 7,
            }
        ],
        "source": {
            "event_id": SNAPSHOT_EVENT_ID,
            "event_type": "bloodbank.v1.lifecycle.snapshot.updated",
            "event_time": NOW,
            "ordering_key": f"lifecycle:{LIFECYCLE_ID}",
        },
    }


def authoritative_reply(command, *, verdict):
    command_data = command["data"]
    applied = verdict == "applied"
    idempotent = verdict == "idempotent"
    accepted = applied or idempotent
    return {
        "specversion": "1.0",
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"reply:{command['id']}:{verdict}")),
        "source": "urn:33god:service:lifecycle",
        "type": "bloodbank.v1.lifecycle.intent.submit",
        "subject": "bloodbank.rpy.v1.lifecycle.intent.submit",
        "time": NOW,
        "datacontenttype": "application/json",
        "dataschema": "apicurio://holyfields/bloodbank.v1.lifecycle.intent.submit.reply/versions/1",
        "correlationid": command["correlationid"],
        "causationid": command["id"],
        "producer": "delorenj/lifecycle",
        "service": "lifecycle",
        "domain": "lifecycle",
        "schemaref": "bloodbank.v1.lifecycle.intent.submit.reply.v1",
        "kind": "reply",
        "actor": {
            "type": "service",
            "agent_id": "delorenj.lifecycle",
            "instance": "test-authority",
        },
        "data": {
            "contract_version": 1,
            "lifecycle_id": command_data["lifecycle_id"],
            "repo": command_data["repo"],
            "reply_to_command_event_id": command["id"],
            "command_id": command["command_id"],
            "idempotency_key": command["idempotency_key"],
            "expected_state_version": command_data["expected_state_version"],
            "observed_state_version": command_data["expected_state_version"],
            "verdict": verdict,
            "mutated": applied,
            "resulting_state_version": (
                command_data["expected_state_version"] + 1 if accepted else None
            ),
            "applied_event_id": str(uuid.uuid4()) if accepted else None,
            "capability_id": command_data["capability"]["capability_id"],
            "reason_code": "TRANSITION_APPLIED" if accepted else "EXPECTED_STATE_VERSION_MISMATCH",
            "responded_at": NOW,
        },
    }


def validate_with_bloodbank(envelope):
    registry = Registry()
    for path in SCHEMAS_ROOT.rglob("*.json"):
        document = json.loads(path.read_text(encoding="utf-8"))
        if "$id" in document:
            registry = registry.with_resource(document["$id"], Resource.from_contents(document))
    relative = SCHEMA_BY_REF[envelope["schemaref"]]
    schema = json.loads((SCHEMAS_ROOT / relative).read_text(encoding="utf-8"))
    Draft202012Validator(
        schema,
        registry=registry,
        format_checker=FormatChecker(),
    ).validate(envelope)
