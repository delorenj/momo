import asyncio
import hashlib
import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

MOMO_ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = MOMO_ROOT / "skill" / "scripts" / "lifecycle_client.py"
WORKER_PATH = MOMO_ROOT / "skill" / "scripts" / "obligation_worker.py"
CATALOG_PATH = MOMO_ROOT / "skill" / "resources" / "obligation-skill-catalog.json"
RESOURCE_PATH = MOMO_ROOT / ".agents" / "skills" / "bmad-code-review" / "SKILL.md"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


client = load_module("momo_lifecycle_client_worker_tests", CLIENT_PATH)
worker = load_module("momo_obligation_worker", WORKER_PATH)

LIFECYCLE_ID = "11111111-1111-4111-8111-111111111111"
SNAPSHOT_CORRELATION_ID = "22222222-2222-4222-8222-222222222222"
SNAPSHOT_EVENT_ID = "33333333-3333-4333-8333-333333333333"
SNAPSHOT_CAUSATION_ID = "44444444-4444-4444-8444-444444444444"
OBLIGATION_INSTANCE_ID = "55555555-5555-4555-8555-555555555555"
ACTOR = {"type": "agent_cli", "agent_id": "momo", "cli": "codex", "provider": "openai"}
STREAM = "BLOODBANK_COMMANDS"
CONSUMER = "aion-momo-obligation-unit"
DELIVERY_SEQUENCE = 42


class FakeMessage:
    def __init__(self, command, operations, *, ack_error=None):
        self.subject = worker.INVOCATION_SUBJECT
        self.data = json.dumps(command, sort_keys=True).encode()
        self.metadata = SimpleNamespace(
            stream=STREAM,
            consumer=CONSUMER,
            sequence=SimpleNamespace(stream=DELIVERY_SEQUENCE, consumer=1),
            num_delivered=1,
            timestamp=datetime(2026, 7, 18, 12, 1, tzinfo=UTC),
            pending=0,
        )
        self.operations = operations
        self.ack_error = ack_error
        self.acked = False

    async def ack_sync(self, *, timeout):
        self.operations.append("ack_sync_called")
        if self.ack_error:
            raise self.ack_error
        self.acked = True


class FakeJetStream:
    def __init__(self, operations, *, publish_error=None, puback=None):
        self.operations = operations
        self.publish_error = publish_error
        self.puback = puback or SimpleNamespace(
            stream="BLOODBANK_EVENTS",
            seq=84,
            duplicate=False,
        )
        self.published_subject = None
        self.published_payload = None

    async def publish(self, subject, payload, *, timeout):
        self.operations.append("publish_called")
        self.published_subject = subject
        self.published_payload = payload
        if self.publish_error:
            raise self.publish_error
        self.operations.append("puback_returned")
        return self.puback


def projection():
    return {
        "lifecycle_id": LIFECYCLE_ID,
        "repo": "delorenj/33GOD",
        "projection_status": "current",
        "state_version": 7,
        "legal_frontier": [],
        "obligations": [
            {
                "id": "independent-review",
                "obligation_instance_id": OBLIGATION_INSTANCE_ID,
                "activated_at": "2026-07-18T11:55:00Z",
                "kind": "independent_review",
                "status": "pending",
                "description": "Obtain independent review.",
                "skill_ref": {"name": "bmad-code-review", "selector": "6.10.2"},
                "owner_id": "agent:independent-reviewer",
                "due_at": None,
                "source_observation_ids": [],
            }
        ],
        "capabilities": [],
        "source": {
            "event_id": SNAPSHOT_EVENT_ID,
            "event_type": "bloodbank.v1.lifecycle.snapshot.updated",
            "event_time": "2026-07-18T12:00:00Z",
            "subject": "bloodbank.evt.v1.lifecycle.snapshot.updated",
            "authority_source": "urn:33god:service:lifecycle",
            "producer": "delorenj/lifecycle",
            "service": "lifecycle",
            "kind": "event",
            "domain": "lifecycle",
            "schema_ref": "bloodbank.v1.lifecycle.snapshot.updated.v3",
            "data_schema": (
                "apicurio://holyfields/bloodbank.v1.lifecycle.snapshot.updated/versions/3"
            ),
            "actor": {
                "type": "service",
                "agent_id": "delorenj.lifecycle",
                "instance": "test-authority",
            },
            "correlation_id": SNAPSHOT_CORRELATION_ID,
            "causation_id": SNAPSHOT_CAUSATION_ID,
            "ordering_key": f"lifecycle:{LIFECYCLE_ID}",
        },
        "provenance": {
            "authority": "delorenj/lifecycle",
            "authority_instance": "test-authority",
            "reconciliation_id": "66666666-6666-4666-8666-666666666666",
            "policy_version": "1.0.0",
            "source_observation_ids": [],
        },
    }


def invocation_plan():
    return client.build_obligation_invocation(
        projection(),
        actor=ACTOR,
        parameters={"review_depth": "bounded-adversarial"},
    )


def expectation_for(plan):
    command = plan["invocation_command"]
    context = command["data"]["context"]
    selection = plan["selection"]
    return {
        "contract": "momo.obligation-worker.expectation.v1",
        "invocation_id": command["id"],
        "lifecycle_id": selection["lifecycle_id"],
        "obligation_id": selection["obligation_id"],
        "obligation_instance_id": selection["obligation_instance_id"],
        "activated_at": selection["activated_at"],
        "target_actor_id": selection["target_actor_id"],
        "expected_state_version": selection["state_version"],
        "authority_snapshot_event_id": selection["authority_snapshot_event_id"],
        "authority_snapshot_event_time": selection["authority_snapshot_event_time"],
        "authority_snapshot_correlation_id": selection[
            "authority_snapshot_correlation_id"
        ],
        "correlation_id": command["correlationid"],
        "causation_id": command["causationid"],
        "skill_ref": context["skill_ref"],
    }


def write_evidence_package(tmp_path, plan, *, bad_assertion=False):
    context = plan["invocation_command"]["data"]["context"]
    authority = {
        "lifecycle_id": context["lifecycle_id"],
        "state_version": context["expected_state_version"],
        "authority_snapshot_event_id": context["authority_snapshot_event_id"],
        "obligation": {
            "id": context["obligation"]["id"],
            "obligation_instance_id": context["obligation"]["obligation_instance_id"],
            "status": "pending",
        },
    }
    authority_path = tmp_path / "authority-snapshot.json"
    authority_bytes = json.dumps(authority, indent=2, sort_keys=True).encode() + b"\n"
    authority_path.write_bytes(authority_bytes)
    package = {
        "schema": "momo.obligation-review-evidence-package.v1",
        "run_id": "unit-current-run",
        "lifecycle_id": context["lifecycle_id"],
        "repo": context["repo"],
        "artifacts": [
            {
                "id": "authority-snapshot",
                "path": authority_path.name,
                "media_type": "application/json",
                "size_bytes": len(authority_bytes),
                "sha256": hashlib.sha256(authority_bytes).hexdigest(),
            }
        ],
        "assertions": [
            {
                "id": "active-occurrence",
                "artifact_id": "authority-snapshot",
                "pointer": "/obligation/obligation_instance_id",
                "equals": "wrong" if bad_assertion else OBLIGATION_INSTANCE_ID,
            },
            {
                "id": "authority-version",
                "artifact_id": "authority-snapshot",
                "pointer": "/state_version",
                "equals": 7,
            },
        ],
    }
    package_path = tmp_path / "evidence-package.json"
    package_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
    return package_path


def process(tmp_path, *, expectation=None, package_path=None, js=None, msg=None):
    plan = invocation_plan()
    operations = []
    expectation = expectation or expectation_for(plan)
    package_path = package_path or write_evidence_package(tmp_path, plan)
    msg = msg or FakeMessage(plan["invocation_command"], operations)
    js = js or FakeJetStream(operations)
    receipt = asyncio.run(
        worker.process_invocation_message(
            message=msg,
            jetstream=js,
            expectation=expectation,
            catalog_path=CATALOG_PATH,
            resource_root=MOMO_ROOT,
            evidence_package_path=package_path,
            report_path=tmp_path / "review-report.md",
            receipt_path=tmp_path / "worker-receipt.json",
            expected_stream=STREAM,
            consumer=CONSUMER,
            clock=lambda: "2026-07-18T12:30:00Z",
            publish_timeout=2.0,
            ack_timeout=2.0,
        )
    )
    return plan, msg, js, operations, receipt


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_actor_id", "agent:other-reviewer"),
        ("obligation_instance_id", "77777777-7777-4777-8777-777777777777"),
        ("authority_snapshot_event_id", "88888888-8888-4888-8888-888888888888"),
        ("correlation_id", "99999999-9999-4999-8999-999999999999"),
        ("causation_id", "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
        ("expected_state_version", 8),
        ("skill_ref", {"name": "bmad-code-review", "selector": "latest"}),
    ],
)
def test_invocation_validation_accepts_only_exact_expected_delivery(field, value):
    plan = invocation_plan()
    expected = expectation_for(plan)
    expected[field] = value

    with pytest.raises(worker.ObligationWorkerError, match=field):
        worker.validate_invocation(plan["invocation_command"], expected)


def test_selector_resolves_exact_promoted_resource_digest(tmp_path):
    binding = worker.resolve_skill_binding(
        {"name": "bmad-code-review", "selector": "6.10.2"},
        catalog_path=CATALOG_PATH,
        resource_root=MOMO_ROOT,
    )

    resource_bytes = RESOURCE_PATH.read_bytes()
    assert binding["resource_path"] == ".agents/skills/bmad-code-review/SKILL.md"
    assert binding["resource_sha256"] == hashlib.sha256(resource_bytes).hexdigest()
    assert binding["adapter"] == "bounded-evidence-review-v1"

    copied_resource = tmp_path / "resource" / "SKILL.md"
    copied_resource.parent.mkdir()
    copied_resource.write_bytes(resource_bytes + b"tampered\n")
    catalog = json.loads(CATALOG_PATH.read_text())
    catalog["bindings"][0]["resource_path"] = "resource/SKILL.md"
    copied_catalog = tmp_path / "catalog.json"
    copied_catalog.write_text(json.dumps(catalog))
    with pytest.raises(worker.ObligationWorkerError, match="digest"):
        worker.resolve_skill_binding(
            {"name": "bmad-code-review", "selector": "6.10.2"},
            catalog_path=copied_catalog,
            resource_root=tmp_path,
        )

    with pytest.raises(worker.ObligationWorkerError, match="not cataloged"):
        worker.resolve_skill_binding(
            {"name": "bmad-code-review", "selector": "7.0.0"},
            catalog_path=CATALOG_PATH,
            resource_root=MOMO_ROOT,
        )


def test_review_report_hash_is_over_exact_written_artifact_bytes(tmp_path):
    plan = invocation_plan()
    binding = worker.resolve_skill_binding(
        plan["selection"]["skill_ref"],
        catalog_path=CATALOG_PATH,
        resource_root=MOMO_ROOT,
    )
    package_path = write_evidence_package(tmp_path, plan)
    report_path = tmp_path / "review-report.md"

    artifact = worker.execute_bounded_review(
        invocation_plan=plan,
        binding=binding,
        evidence_package_path=package_path,
        report_path=report_path,
    )

    exact_bytes = report_path.read_bytes()
    assert artifact["size_bytes"] == len(exact_bytes)
    assert artifact["sha256"] == hashlib.sha256(exact_bytes).hexdigest()
    assert artifact["sha256"] != artifact["sha256"][0] * 64
    assert b"active-occurrence" in exact_bytes
    assert b"authority-version" in exact_bytes
    assert binding["resource_sha256"].encode() in exact_bytes


def test_completion_puback_precedes_invocation_ack_and_receipt_links_identity(tmp_path):
    plan, msg, js, operations, receipt = process(tmp_path)
    exact_artifact = (tmp_path / "review-report.md").read_bytes()
    persisted = json.loads((tmp_path / "worker-receipt.json").read_text())
    completion = json.loads(js.published_payload)

    assert msg.acked is True
    assert operations.index("puback_returned") < operations.index("ack_sync_called")
    assert receipt == persisted
    assert persisted["delivery"] == {
        "stream": STREAM,
        "consumer": CONSUMER,
        "stream_sequence": DELIVERY_SEQUENCE,
        "consumer_sequence": 1,
        "num_delivered": 1,
    }
    assert persisted["invocation"]["id"] == plan["invocation_command"]["id"]
    assert persisted["artifact"]["size_bytes"] == len(exact_artifact)
    assert persisted["artifact"]["sha256"] == hashlib.sha256(exact_artifact).hexdigest()
    assert persisted["completion"]["event_id"] == completion["id"]
    assert persisted["completion"]["stream"] == "BLOODBANK_EVENTS"
    assert persisted["completion"]["stream_sequence"] == 84
    ordered = [item["operation"] for item in persisted["operation_order"]]
    assert ordered.index("completion_puback") < ordered.index("invocation_ack_sync")


@pytest.mark.parametrize("failure_stage", ["validation", "adapter", "hash", "publish"])
def test_validation_adapter_hash_and_publish_failures_never_ack(
    tmp_path, monkeypatch, failure_stage
):
    plan = invocation_plan()
    operations = []
    expectation = expectation_for(plan)
    package_path = write_evidence_package(
        tmp_path,
        plan,
        bad_assertion=failure_stage == "adapter",
    )
    if failure_stage == "validation":
        expectation["target_actor_id"] = "agent:wrong"
    if failure_stage == "hash":
        monkeypatch.setattr(worker, "hash_artifact_file", lambda _path: "0" * 64)
    js = FakeJetStream(
        operations,
        publish_error=RuntimeError("no completion PubAck") if failure_stage == "publish" else None,
    )
    msg = FakeMessage(plan["invocation_command"], operations)

    with pytest.raises((worker.ObligationWorkerError, RuntimeError)):
        asyncio.run(
            worker.process_invocation_message(
                message=msg,
                jetstream=js,
                expectation=expectation,
                catalog_path=CATALOG_PATH,
                resource_root=MOMO_ROOT,
                evidence_package_path=package_path,
                report_path=tmp_path / "review-report.md",
                receipt_path=tmp_path / "worker-receipt.json",
                expected_stream=STREAM,
                consumer=CONSUMER,
                clock=lambda: "2026-07-18T12:30:00Z",
                publish_timeout=2.0,
                ack_timeout=2.0,
            )
        )

    assert msg.acked is False
    assert "ack_sync_called" not in operations
    assert not (tmp_path / "worker-receipt.json").exists()
