#!/usr/bin/env python3
"""Regression tests for the six Momo hardening tickets (33GPM-3 through 33GPM-8).

Run: python3 momo/skill/scripts/tests/test_momo_hardening.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[4]  # 33GOD root
LIB = ROOT / "momo" / "skill" / "scripts" / "lib"
SCRIPTS = ROOT / "momo" / "skill" / "scripts"

sys.path.insert(0, str(LIB))


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
