#!/usr/bin/env python3
"""Regression tests for the six Momo hardening tickets (33GPM-3 through 33GPM-8).

Run: python3 momo/skill/scripts/tests/test_momo_hardening.py
"""
import json
import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import pathlib
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[4]  # 33GOD root
LIB = ROOT / "momo" / "skill" / "scripts" / "lib"
SCRIPTS = ROOT / "momo" / "skill" / "scripts"

sys.path.insert(0, str(LIB))

from momo_lane_gate import GateResult, LaneGate

TRELLO_SPEC = importlib.util.spec_from_file_location(
    "momo_trello_provider",
    SCRIPTS / "providers" / "trello.py",
)
assert TRELLO_SPEC is not None and TRELLO_SPEC.loader is not None
trello_provider = importlib.util.module_from_spec(TRELLO_SPEC)
TRELLO_SPEC.loader.exec_module(trello_provider)


def run_cli(script: str, *args, cwd=None, env=None):
    """Run a momo CLI script and return (rc, stdout, stderr)."""
    e = os.environ.copy()
    if env:
        e.update(env)
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=cwd or str(ROOT),
        capture_output=True, text=True, timeout=15, env=e,
    )
    return r.returncode, r.stdout.strip(), r.stderr.strip()


class TestHandback(unittest.TestCase):
    """33GPM-3: Structured worker hand-back with heartbeat and retry policy."""

    def setUp(self):
        self.spool = tempfile.mkdtemp(prefix="momo-hb-test-")

    def tearDown(self):
        shutil.rmtree(self.spool, ignore_errors=True)

    def test_init_creates_bundle(self):
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "init", "--agent-id", "worker-1")
        self.assertEqual(rc, 0, err)
        bundle_path = pathlib.Path(self.spool) / "T-1.handback.json"
        self.assertTrue(bundle_path.exists())
        data = json.loads(bundle_path.read_text())
        self.assertEqual(data["issue"], "T-1")
        self.assertEqual(data["worker"]["agent_id"], "worker-1")
        self.assertIn("heartbeat", data)
        self.assertIn("checks", data)

    def test_heartbeat_updates_timestamp(self):
        run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "init", "--agent-id", "w")
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "heartbeat")
        self.assertEqual(rc, 0, err)
        bundle = json.loads((pathlib.Path(self.spool) / "T-1.handback.json").read_text())
        self.assertNotEqual(bundle["heartbeat"]["started_at"], bundle["heartbeat"]["last_seen_at"])

    def test_finalize_and_validate(self):
        run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "init", "--agent-id", "w")
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "finalize", "--status", "DONE", "--summary", "all pass", "--tests")
        self.assertEqual(rc, 0, err)
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "T-1", "--spool", self.spool, "validate")
        self.assertEqual(rc, 0, err)
        self.assertIn("VALID", out)

    def test_validate_fails_on_missing_bundle(self):
        rc, out, err = run_cli("momo-worker-handback.py", "--issue", "NOPE", "--spool", self.spool, "validate")
        self.assertNotEqual(rc, 0)


class TestFindingsLedger(unittest.TestCase):
    """33GPM-6: Stable findings ledger."""

    def setUp(self):
        self.findings_dir = ROOT / "_bmad-output" / "implementation-artifacts" / "findings"
        self.findings_dir.mkdir(parents=True, exist_ok=True)
        # Clean test artifacts
        for f in self.findings_dir.glob("TESTFINDINGS*"):
            f.unlink()

    def tearDown(self):
        for f in self.findings_dir.glob("TESTFINDINGS*"):
            f.unlink()

    def test_add_and_show(self):
        rc, out, err = run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-1", "add", "--severity", "high", "--category", "security", "--description", "test finding")
        self.assertEqual(rc, 0, err)
        self.assertEqual(out, "F001")

    def test_resolve_with_dash_id(self):
        run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-1", "add", "--severity", "high", "--category", "bug", "--description", "test")
        rc, out, err = run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-1", "resolve", "--id", "F-001")
        self.assertEqual(rc, 0, err)
        rc, out, err = run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-1", "show")
        data = json.loads(out)
        self.assertEqual(data["findings"][0]["state"], "resolved")

    def test_stable_ids(self):
        for i in range(3):
            run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-2", "add", "--severity", "low", "--category", "style", "--description", f"finding {i}")
        rc, out, err = run_cli("momo-findings-ledger.py", "--issue", "TESTFINDINGS-2", "show")
        data = json.loads(out)
        ids = [f["id"] for f in data["findings"]]
        self.assertEqual(ids, ["F001", "F002", "F003"])

    def tearDown2(self):
        for f in self.findings_dir.glob("TESTFINDINGS*"):
            f.unlink()


class TestTreeLock(unittest.TestCase):
    """33GPM-8: Lock working tree against background auto-commits."""

    def setUp(self):
        self.lock_dir = ROOT / ".momo"
        # Clean any test locks
        for f in self.lock_dir.glob("tree.lock*"):
            f.unlink()

    def tearDown(self):
        for f in self.lock_dir.glob("tree.lock*"):
            f.unlink()

    def test_acquire_status_release(self):
        rc, out, err = run_cli("momo-tree-lock.py", "acquire", "--owner", "test-owner")
        self.assertEqual(rc, 0, err)
        self.assertIn("ACQUIRED", out)

        rc, out, err = run_cli("momo-tree-lock.py", "status")
        self.assertEqual(rc, 0, err)
        data = json.loads(out)
        self.assertTrue(data["locked"])
        self.assertEqual(data["owner"], "test-owner")

        rc, out, err = run_cli("momo-tree-lock.py", "release", "--owner", "test-owner")
        self.assertEqual(rc, 0, err)
        self.assertIn("RELEASED", out)

    def test_guard_blocks_when_locked(self):
        run_cli("momo-tree-lock.py", "acquire", "--owner", "session-1")
        rc, out, err = run_cli("momo-tree-lock.py", "guard")
        self.assertNotEqual(rc, 0, err)
        self.assertIn("GUARD_FAIL", err)

    def test_guard_passes_when_unlocked(self):
        rc, out, err = run_cli("momo-tree-lock.py", "guard")
        self.assertEqual(rc, 0, err)


class TestReporter(unittest.TestCase):
    """33GPM-5: Reporting discipline and deduplication."""

    def test_dry_run_produces_json(self):
        rc, out, err = run_cli("momo-reporter.py", "--issue", "T-1", "--event", "impl-complete", "--delta", "all done", "--state", "review", "--dry-run")
        self.assertEqual(rc, 0, err)
        data = json.loads(out)
        self.assertTrue(data["skipped"])
        self.assertIn("hash", data)
        self.assertIn("body", data)


class TestLaneGate(unittest.TestCase):
    """33GPM-7: Gated lane transitions."""

    def make_gate(self, temp: str) -> LaneGate:
        root = pathlib.Path(temp)
        script = (
            root
            / "agents"
            / "hermes"
            / "pm"
            / ".scripts"
            / "sentinel"
            / "bin"
            / "issue-autonomous-review.sh"
        )
        script.parent.mkdir(parents=True)
        script.touch()
        gate = LaneGate(root, "T-1")
        gate.gate_tree_lock = mock.Mock(
            return_value=GateResult("tree_lock", True, "pass")
        )
        gate.gate_close = mock.Mock(
            return_value=GateResult("close_gate", True, "pass")
        )
        return gate

    def test_gate_blocks_without_evidence(self):
        rc, out, err = run_cli("momo-lane-gate.py", "--issue", "NONEXISTENT-1", "--target", "completed", "--no-review")
        self.assertNotEqual(rc, 0)
        data = json.loads(out)
        self.assertFalse(data["allowed"])

    def test_gate_blocks_without_review(self):
        rc, out, err = run_cli("momo-lane-gate.py", "--issue", "NONEXISTENT-2", "--target", "in_review", "--no-review")
        self.assertNotEqual(rc, 0)
        # gate prints JSON to stdout even on failure
        data = json.loads(out)
        self.assertFalse(data["allowed"])

    def test_completed_review_is_single_close_authority(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            review = pathlib.Path(temp) / "T-1.review.md"
            gate._run = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [], 0, stdout="AUTONOMOUS REVIEW: ACCEPTED\n", stderr=""
                )
            )
            gate.transition = mock.Mock()

            result = gate.run("completed", review_file=review)

            self.assertTrue(result["allowed"])
            self.assertEqual(result["transition_authority"], "autonomous_review")
            gate._run.assert_called_once_with(
                [
                    str(gate.sentinel_bin / "issue-autonomous-review.sh"),
                    "T-1",
                    str(review),
                    "--close",
                ]
            )
            gate.transition.assert_not_called()
            self.assertNotIn("stays in the review lane", json.dumps(result).lower())

    def test_completed_transition_failure_is_not_accepted_or_retried(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            gate._run = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [], 1, stdout="", stderr="adapter transition failed"
                )
            )
            gate.transition = mock.Mock()

            result = gate.run("completed")

            self.assertFalse(result["allowed"])
            self.assertIn("adapter transition failed", json.dumps(result))
            self.assertNotIn("accepted", json.dumps(result).lower())
            gate.transition.assert_not_called()
            gate._run.assert_called_once()

    def test_completed_comment_failure_remains_explicit(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            gate._run = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [],
                    1,
                    stdout="AUTONOMOUS REVIEW: ACCEPTED\n",
                    stderr="required acceptance comment failed",
                )
            )
            gate.transition = mock.Mock()

            result = gate.run("completed")

            rendered = json.dumps(result).lower()
            self.assertFalse(result["allowed"])
            self.assertIn("required acceptance comment failed", rendered)
            self.assertNotIn("autonomous review: accepted", rendered)
            self.assertNotIn("stays in the review lane", rendered)
            gate.transition.assert_not_called()

    def test_review_lane_reports_success_only_after_transition(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            gate.transition = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [], 0, stdout='{"ok":true}', stderr=""
                )
            )

            result = gate.run("in_review")

            self.assertTrue(result["allowed"])
            gate.transition.assert_called_once_with("in_review")
            self.assertNotIn("accepted", json.dumps(result).lower())

    def test_review_lane_transition_failure_has_no_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="momo-lane-test-") as temp:
            gate = self.make_gate(temp)
            gate.transition = mock.Mock(
                return_value=subprocess.CompletedProcess(
                    [], 1, stdout="", stderr="transition failed"
                )
            )

            result = gate.run("in_review")

            self.assertFalse(result["allowed"])
            self.assertIn("transition failed", result["adapter_error"])
            self.assertNotIn("accepted", json.dumps(result).lower())


class FakeTrello:
    def __init__(self, lists, card_gets, put_response, post_response=None, cards=None):
        self.lists = lists
        self.card_gets = list(card_gets)
        self.put_response = put_response
        self.post_response = post_response
        self.cards = cards
        self.calls = []

    def get(self, path, extra=None):
        self.calls.append(("GET", path, extra))
        if path.startswith("boards/"):
            if path.endswith("/cards") and self.cards is not None:
                return self.cards
            return self.lists
        if path.startswith("cards/") and self.card_gets:
            return self.card_gets.pop(0)
        raise AssertionError(f"unexpected GET {path}")

    def put(self, path, extra=None):
        self.calls.append(("PUT", path, extra))
        return self.put_response

    def post(self, path, extra=None):
        self.calls.append(("POST", path, extra))
        return self.post_response


class TestTrelloTransition(unittest.TestCase):
    def transition(self, fake, card_ref="card-1", target="completed", config=None):
        config = config or {}
        return trello_provider.transition_card(
            fake,
            "board-1",
            card_ref,
            target,
            config,
            trello_provider.lane_map(config),
        )

    def assert_transition_error(self, fake, expected):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.transition(fake)
        self.assertIn(expected, stderr.getvalue())

    def test_duplicate_exact_or_casefold_lane_is_rejected_without_put(self):
        for names in (("Done", "Done"), ("Done", "done")):
            with self.subTest(names=names):
                fake = FakeTrello(
                    [
                        {"id": "list-1", "name": names[0]},
                        {"id": "list-2", "name": names[1]},
                    ],
                    [],
                    {},
                )

                self.assert_transition_error(fake, "duplicate live lanes")

                self.assertFalse(any(call[0] == "PUT" for call in fake.calls))

    def assert_transition_scope_error(self, card, expected):
        fake = FakeTrello(
            [{"id": "list-done", "name": "Done"}],
            [card],
            {},
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            self.transition(fake)

        self.assertIn(expected, stderr.getvalue())
        self.assertEqual([call[0] for call in fake.calls], ["GET", "GET"])
        self.assertEqual(fake.calls[1], (
            "GET",
            "cards/card-1",
            {"fields": "id,idBoard,idList,shortLink,idShort"},
        ))

    def test_transition_rejects_wrong_board_before_put(self):
        self.assert_transition_scope_error(
            {"id": "card-1", "idBoard": "board-2", "idList": "list-old"},
            "different board",
        )

    def test_transition_rejects_missing_or_malformed_board_before_put(self):
        for card in (
            {"id": "card-1", "idList": "list-old"},
            {"id": "card-1", "idBoard": 123, "idList": "list-old"},
            {"id": "card-1", "idBoard": "", "idList": "list-old"},
        ):
            with self.subTest(card=card):
                self.assert_transition_scope_error(card, "valid idBoard")

    def test_transition_rejects_wrong_or_malformed_native_id_before_put(self):
        for card in (
            {"id": "card-2", "idBoard": "board-1", "idList": "list-old"},
            {"id": 123, "idBoard": "board-1", "idList": "list-old"},
            {"idBoard": "board-1", "idList": "list-old"},
        ):
            with self.subTest(card=card):
                expected = (
                    "different card"
                    if card.get("id") == "card-2"
                    else "without an id"
                )
                self.assert_transition_scope_error(card, expected)

    def test_wrong_put_response_fails_before_readback(self):
        wrong_responses = (
            {},
            {"id": "different-card", "idList": "list-done"},
            {"id": "card-1", "idList": "different-list"},
        )
        for response in wrong_responses:
            with self.subTest(response=response):
                fake = FakeTrello(
                    [{"id": "list-done", "name": "Done"}],
                    [
                        {
                            "id": "card-1",
                            "idBoard": "board-1",
                            "idShort": 42,
                            "idList": "list-old",
                        },
                        {"id": "card-1", "idShort": 42, "idList": "list-done"},
                    ],
                    response,
                )

                self.assert_transition_error(fake, "PUT response")

                self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)
                self.assertEqual(len(fake.card_gets), 1)

    def test_wrong_or_missing_readback_fails_without_ok(self):
        wrong_readbacks = (
            {},
            {"id": "different-card", "idShort": 42, "idList": "list-done"},
            {"id": "card-1", "idShort": 42, "idList": "different-list"},
        )
        for readback in wrong_readbacks:
            with self.subTest(readback=readback):
                fake = FakeTrello(
                    [{"id": "list-done", "name": "Done"}],
                    [
                        {
                            "id": "card-1",
                            "idBoard": "board-1",
                            "idShort": 42,
                            "idList": "list-old",
                        },
                        readback,
                    ],
                    {"id": "card-1", "idList": "list-done"},
                )

                self.assert_transition_error(fake, "GET readback")

                self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)

    def test_exact_transition_puts_once_and_reads_back_same_card(self):
        fake = FakeTrello(
            [{"id": "list-done", "name": "Done"}],
            [
                {
                    "id": "card-1",
                    "idBoard": "board-1",
                    "idShort": 42,
                    "shortLink": "abc123",
                    "idList": "list-old",
                },
                {
                    "id": "card-1",
                    "idShort": 42,
                    "shortLink": "abc123",
                    "idList": "list-done",
                },
            ],
            {"id": "card-1", "idList": "list-done"},
        )

        result = self.transition(fake)

        self.assertEqual(
            result,
            {
                "ok": True,
                "card": "card-1",
                "requested_card": "card-1",
                "target": "completed",
                "moved_to": "Done",
                "state": "completed",
            },
        )
        self.assertEqual(
            [call[:2] for call in fake.calls],
            [
                ("GET", "boards/board-1/lists"),
                ("GET", "cards/card-1"),
                ("PUT", "cards/card-1"),
                ("GET", "cards/card-1"),
            ],
        )
        self.assertEqual(sum(call[0] == "PUT" for call in fake.calls), 1)
        self.assertEqual(
            fake.calls[1][2],
            {"fields": "id,idBoard,idList,shortLink,idShort"},
        )

    def test_default_cancelled_transition_uses_normalized_lane(self):
        fake = FakeTrello(
            [{"id": "list-cancelled", "name": "Cancelled"}],
            [
                {
                    "id": "card-1",
                    "idBoard": "board-1",
                    "idShort": 42,
                    "idList": "list-old",
                },
                {"id": "card-1", "idShort": 42, "idList": "list-cancelled"},
            ],
            {"id": "card-1", "idList": "list-cancelled"},
        )

        result = self.transition(fake, target="cancelled")

        self.assertEqual(result["state"], "cancelled")
        self.assertEqual(result["moved_to"], "Cancelled")
        self.assertEqual(fake.calls[2], (
            "PUT",
            "cards/card-1",
            {"idList": "list-cancelled"},
        ))

    def test_custom_cancelled_transition_honors_write_mapping(self):
        config = {
            "lanes": {"cancelled": ["Abandoned"]},
            "write_targets": {"cancelled": "Abandoned"},
        }
        fake = FakeTrello(
            [{"id": "list-abandoned", "name": "Abandoned"}],
            [
                {
                    "id": "card-1",
                    "idBoard": "board-1",
                    "idShort": 42,
                    "idList": "list-old",
                },
                {"id": "card-1", "idShort": 42, "idList": "list-abandoned"},
            ],
            {"id": "card-1", "idList": "list-abandoned"},
        )

        result = self.transition(
            fake,
            target="cancelled",
            config=config,
        )

        self.assertEqual(result["state"], "cancelled")
        self.assertEqual(result["moved_to"], "Abandoned")
        self.assertEqual(fake.calls[2][2], {"idList": "list-abandoned"})


class TestTrelloComment(unittest.TestCase):
    CARD = {
        "id": "card-1",
        "idBoard": "board-1",
        "idShort": 42,
        "shortLink": "abc123",
    }

    def comment(self, response):
        fake = FakeTrello(
            [],
            [dict(self.CARD)],
            {},
            post_response=response,
        )
        result = trello_provider.comment_card(
            fake,
            "board-1",
            "card-1",
            "Finished closeout",
        )
        return result, fake

    def assert_comment_error(self, response, expected):
        fake = FakeTrello(
            [],
            [dict(self.CARD)],
            {},
            post_response=response,
        )
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            trello_provider.comment_card(
                fake,
                "board-1",
                "card-1",
                "Finished closeout",
            )
        self.assertIn(expected, stderr.getvalue())
        self.assertEqual(sum(call[0] == "POST" for call in fake.calls), 1)

    def assert_comment_scope_error(self, card, expected):
        fake = FakeTrello(
            [],
            [card],
            {},
            post_response={"id": "action-1"},
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit):
            trello_provider.comment_card(
                fake,
                "board-1",
                "card-1",
                "Finished closeout",
            )

        self.assertIn(expected, stderr.getvalue())
        self.assertEqual(fake.calls, [(
            "GET",
            "cards/card-1",
            {"fields": "id,idBoard,shortLink,idShort"},
        )])

    def test_comment_rejects_wrong_board_before_post(self):
        self.assert_comment_scope_error(
            {"id": "card-1", "idBoard": "board-2"},
            "different board",
        )

    def test_comment_rejects_missing_or_malformed_board_before_post(self):
        for card in (
            {"id": "card-1"},
            {"id": "card-1", "idBoard": 123},
            {"id": "card-1", "idBoard": ""},
        ):
            with self.subTest(card=card):
                self.assert_comment_scope_error(card, "valid idBoard")

    def test_comment_rejects_wrong_or_malformed_native_id_before_post(self):
        for card in (
            {"id": "card-2", "idBoard": "board-1"},
            {"id": 123, "idBoard": "board-1"},
            {"idBoard": "board-1"},
        ):
            with self.subTest(card=card):
                expected = (
                    "different card"
                    if card.get("id") == "card-2"
                    else "without an id"
                )
                self.assert_comment_scope_error(card, expected)

    def test_comment_rejects_empty_malformed_or_missing_id_response(self):
        invalid = (
            (None, "action object"),
            ([], "action object"),
            ({}, "no action id"),
            ({"comment": {"id": "action-1"}}, "no action id"),
            ({"id": ""}, "no action id"),
            ({"id": 123}, "no action id"),
            ({"id": "action-1", "type": "updateCard"}, "action type"),
            ({"id": "action-1", "data": "wrong"}, "data envelope"),
            ({"id": "action-1", "data": {"card": {}}}, "no identity"),
        )
        for response, expected in invalid:
            with self.subTest(response=response):
                self.assert_comment_error(response, expected)

    def test_comment_rejects_wrong_exposed_card(self):
        wrong_cards = (
            {"id": "action-1", "idCard": "card-2"},
            {"id": "action-1", "card": {"id": "card-2"}},
            {"id": "action-1", "data": {"card": {"id": "card-2"}}},
            {
                "id": "action-1",
                "data": {"card": {"id": "card-2", "idShort": 42}},
            },
        )
        for response in wrong_cards:
            with self.subTest(response=response):
                self.assert_comment_error(response, "different card")

    def test_comment_returns_only_proven_action_id(self):
        response = {
            "id": "action-1",
            "type": "commentCard",
            "data": {"card": {"id": "card-1", "idShort": 42}},
        }

        result, fake = self.comment(response)

        self.assertEqual(result, "action-1")
        self.assertEqual(
            [call[:2] for call in fake.calls],
            [
                ("GET", "cards/card-1"),
                ("POST", "cards/card-1/actions/comments"),
            ],
        )
        self.assertEqual(
            fake.calls[0][2],
            {"fields": "id,idBoard,shortLink,idShort"},
        )

    def test_comment_accepts_id_only_response_when_card_is_not_exposed(self):
        result, _fake = self.comment({"id": "action-1"})

        self.assertEqual(result, "action-1")

    def test_comment_cli_prints_nothing_until_response_is_proven(self):
        with tempfile.TemporaryDirectory(prefix="momo-trello-comment-") as temp:
            root = pathlib.Path(temp)
            (root / ".project.json").write_text(json.dumps({
                "ticket_provider": {"type": "trello", "board_id": "board-1"},
            }))
            fake = FakeTrello(
                [],
                [dict(self.CARD)],
                {},
                post_response={},
            )
            stdout = io.StringIO()
            stderr = io.StringIO()
            argv = [
                "trello.py",
                "--root",
                str(root),
                "comment",
                "card-1",
                "Finished closeout",
            ]
            with (
                mock.patch.object(trello_provider.sys, "argv", argv),
                mock.patch.object(
                    trello_provider,
                    "creds",
                    return_value=("key", "token"),
                ),
                mock.patch.object(trello_provider, "Trello", return_value=fake),
                contextlib.redirect_stdout(stdout),
                contextlib.redirect_stderr(stderr),
                self.assertRaises(SystemExit),
            ):
                trello_provider.main()

            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("no action id", stderr.getvalue())


class TestTrelloCancelledClassification(unittest.TestCase):
    def run_list_issues(self, config):
        with tempfile.TemporaryDirectory(prefix="momo-trello-list-") as temp:
            root = pathlib.Path(temp)
            (root / ".project.json").write_text(json.dumps({
                "ticket_provider": {"type": "trello", "board_id": "board-1"},
            }))
            if config:
                momo = root / ".momo"
                momo.mkdir()
                (momo / "config.json").write_text(json.dumps(config))

            lane = "Abandoned" if config else "Cancelled"
            fake = FakeTrello(
                [{"id": "list-cancelled", "name": lane}],
                [],
                {},
                cards=[{
                    "id": "card-1",
                    "name": "Cancelled work",
                    "idList": "list-cancelled",
                    "shortLink": "abc123",
                }],
            )
            stdout = io.StringIO()
            argv = ["trello.py", "--root", str(root), "list_issues"]
            with (
                mock.patch.object(trello_provider.sys, "argv", argv),
                mock.patch.object(trello_provider, "creds", return_value=("key", "token")),
                mock.patch.object(trello_provider, "Trello", return_value=fake),
                contextlib.redirect_stdout(stdout),
            ):
                self.assertEqual(trello_provider.main(), 0)
            return json.loads(stdout.getvalue())

    def test_list_issues_classifies_default_cancelled_lane(self):
        rows = self.run_list_issues({})

        self.assertEqual(rows[0]["state"], "cancelled")
        self.assertEqual(rows[0]["state_type"], "cancelled")

    def test_list_issues_classifies_custom_cancelled_lane(self):
        rows = self.run_list_issues({
            "lanes": {"cancelled": ["Abandoned"]},
            "write_targets": {"cancelled": "Abandoned"},
        })

        self.assertEqual(rows[0]["state"], "cancelled")
        self.assertEqual(rows[0]["list"], "Abandoned")


class TestEvidenceCapture(unittest.TestCase):
    """33GPM-4: Automate evidence capture."""

    def test_requires_handback(self):
        rc, out, err = run_cli("momo-evidence-capture.py", "--issue", "NOHANDBACK-1", "--pytest-cmd", "echo", "--ruff-cmd", "echo")
        self.assertNotEqual(rc, 0)
        self.assertIn("no handback bundle", err)


class TestConfigDrift(unittest.TestCase):
    """Verify the current 33GOD project identifier does not drift."""

    def test_project_json_identifier(self):
        data = json.loads((ROOT / ".project.json").read_text())
        self.assertEqual(data["ticket_provider"]["identifier"], "33GOD")

    def test_role_yaml_identifier(self):
        text = (ROOT / "agents" / "hermes" / "pm" / "role.yaml").read_text()
        self.assertIn("33GOD", text)
        # Check the identifier line specifically, not the word "PROJECT" in comments
        for line in text.splitlines():
            if line.strip().startswith("identifier:"):
                self.assertIn("33GOD", line)
                self.assertNotIn("PROJ\"", line)
                break
        else:
            self.fail("no identifier: line found in role.yaml")


class TestBoardCredentialPreflight(unittest.TestCase):
    """JIMB-207: The wrapper recognizes provider-owned fleet credentials."""

    def test_fleet_op_reference_suppresses_false_missing_key_warning(self):
        with tempfile.TemporaryDirectory(prefix="momo-board-test-") as temp:
            root = pathlib.Path(temp) / "repo"
            role = root / "agents" / "hermes" / "pm"
            adapter = role / ".scripts" / "lib" / "ticket-provider.sh"
            adapter.parent.mkdir(parents=True)
            (root / ".project.json").write_text(json.dumps({
                "ticket_provider": {"type": "plane", "workspace": "test.space-name"},
                "agents": {"test-pm": {"role_dir": "agents/hermes/pm"}},
            }))
            adapter.write_text('tp() { printf \'{"provider":"plane"}\\n\'; }\n')

            marker = pathlib.Path(temp) / "must-not-exist"
            fleet_env = pathlib.Path(temp) / "fleet.env"
            fleet_env.write_text("\n".join([
                f"UNRELATED=$(touch {marker})",
                "PLANE_TEST_SPACE_NAME_API_KEY=op://Example/Plane/apiKey",
            ]) + "\n")
            env = os.environ.copy()
            env.pop("PLANE_API_KEY", None)
            env.pop("PLANE_TEST_SPACE_NAME_API_KEY", None)
            env["HERMES_FLEET_ENV"] = str(fleet_env)

            result = subprocess.run(
                ["bash", str(SCRIPTS / "momo-board.sh"), "--root", str(root), "resolve"],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                timeout=15,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("momo-board: WARN", result.stderr)
            self.assertNotIn("op://", result.stdout + result.stderr)
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
