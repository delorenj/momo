#!/usr/bin/env python3
"""momo-hermes-adapter — render a Hermes agent from the Momo spec + per-repo identity.

SKELETON (design draft). Lives (proposed) at:
    ~/code/33GOD/momo/adapter/render_agent.py
invoked by the skill `momo-hermes-adapter` (member of the `ecosystem` hub,
sibling of `agent-fleet-operations`).

Composition with the EXISTING pipeline
--------------------------------------
This adapter does NOT replace the copier template. It is a translator +
overlay around it:

  Momo spec (identity-agnostic)                 per-repo identity (copier vars)
        \\                                          /
         \\----------------  render_agent.py  -----/
                                  |
                 1. build copier answers  (agent_purpose, soul_tone,
                    ticket_provider, model, + spec-derived SOUL sections)
                                  |
                 2. copier copy/update  gh:delorenj/hermes-agent-template
                    -> renders role.yaml.jinja + SOUL.md.jinja
                    -> runs post-gen _tasks 00..99 UNCHANGED
                                  |
                 3. post-render overlays:
                    a. merge config.overlay.yaml -> runtime/config.yaml
                       (honcho neutralization)
                    b. export MOMO_AGENT_ID=<repo_slug>-momo for record-decision
                    c. (until template PR lands) rewrite SOUL.md
                       Role-behavior / Tone / Memory-hygiene from spec

The copier template stays generic + upstreamable. All Momo-specific behavior
is data in the spec, applied here. Fan-out of the spec across repos rides
skillex (skill_ssot.py / agent-config-fanout), NOT Toad (retired 2026-07-15).
"""
from __future__ import annotations
import argparse, os, subprocess, sys, pathlib
import yaml  # PyYAML

TEMPLATE = "gh:delorenj/hermes-agent-template"   # canonical; live checkout at pjangler/templates/hermes-agent
SPEC_DEFAULT = os.path.expanduser("~/code/33GOD/momo/spec/momo-agent.spec.yaml")


def repo_slug(repo_root: pathlib.Path) -> str:
    """Worktree-safe bank/slug = basename(dirname(realpath(git-common-dir)))."""
    try:
        cd = subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"],
            text=True).strip()
        common = pathlib.Path(cd)
        if not common.is_absolute():
            common = (repo_root / common)
        return common.resolve().parent.name
    except Exception:
        return repo_root.name


def load_spec(path: str) -> dict:
    return yaml.safe_load(pathlib.Path(path).read_text())


def build_copier_data(spec: dict, *, repo: str, role: str, slug: str,
                      ticket_provider: str, soul_tone: str | None,
                      model_provider: str, model_name: str) -> dict:
    r = spec["roles"][role]
    tone = soul_tone or spec["personality"]["default_tone"]
    return {
        # identity (copier-owned)
        "target_repo": repo,
        "role": role,
        "ticket_provider": ticket_provider,
        "model_provider": model_provider,
        "model_name": model_name,
        "soul_tone": tone,
        # spec-derived answers (translate generic -> copier vars)
        "agent_purpose": r["purpose_template"].format(repo=repo),
        # NEW copier vars (require the template PR below; until then applied as
        # a post-render SOUL.md rewrite in step 3c):
        "soul_role_behavior": r.get("charter", "").strip(),
        "soul_tone_text": spec["personality"]["tones"][tone],
        "soul_memory_hygiene": spec["memory"]["hygiene"].format(repo_slug=slug),
        "soul_bloodbank_events": r.get("bloodbank_events", []),
        # role.yaml reconcile knobs from spec.behavior
        "reconcile_enabled": r.get("behavior", {}).get("reconcile", {}).get("enabled", False),
        "reconcile_grace_hours": r.get("behavior", {}).get("reconcile", {}).get("grace_hours", 0),
        "reconcile_auto_review": r.get("behavior", {}).get("reconcile", {}).get("auto_review", True),
    }


def run_copier(dst: pathlib.Path, data: dict, update: bool) -> None:
    verb = "update" if update else "copy"
    argv = ["copier", verb, TEMPLATE, str(dst)]
    for k, v in data.items():
        argv += ["--data", f"{k}={v if not isinstance(v, (list, dict)) else yaml.safe_dump(v).strip()}"]
    print("[adapter] $", " ".join(argv))
    # subprocess.run(argv, check=True)   # (skeleton: not executed)


def apply_memory_overlay(runtime_cfg: pathlib.Path, overlay_path: pathlib.Path) -> None:
    """Deep-merge the honcho-neutralization overlay INTO runtime/config.yaml.

    Mirrors hermes _deep_merge semantics: dict values recurse, scalars/lists
    from the overlay win. Idempotent.
    """
    overlay = yaml.safe_load(overlay_path.read_text()) or {}
    base = yaml.safe_load(runtime_cfg.read_text()) if runtime_cfg.exists() else {}
    merged = _deep_merge(base or {}, overlay)
    print(f"[adapter] would write neutralized memory config -> {runtime_cfg}")
    # runtime_cfg.write_text(yaml.safe_dump(merged, sort_keys=False))  # (skeleton)


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v   # scalar/list overrides win (matches hermes _deep_merge)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="target repo name (== copier target_repo)")
    ap.add_argument("--repo-root", default=".", help="path to the repo (for slug/worktree resolution)")
    ap.add_argument("--role", default="pm")
    ap.add_argument("--ticket-provider", default="plane", choices=["plane", "linear", "trello"])
    ap.add_argument("--soul-tone", default=None)
    ap.add_argument("--model-provider", default="")
    ap.add_argument("--model-name", default="")
    ap.add_argument("--spec", default=SPEC_DEFAULT)
    ap.add_argument("--dst", required=True, help="role dir, e.g. ./agents/hermes/pm")
    ap.add_argument("--update", action="store_true", help="copier update (re-render) vs copy")
    ap.add_argument("--overlay", default=str(pathlib.Path(__file__).with_name("config.overlay.yaml")))
    args = ap.parse_args()

    repo_root = pathlib.Path(args.repo_root).resolve()
    slug = repo_slug(repo_root)
    spec = load_spec(args.spec)

    data = build_copier_data(
        spec, repo=args.repo, role=args.role, slug=slug,
        ticket_provider=args.ticket_provider, soul_tone=args.soul_tone,
        model_provider=args.model_provider, model_name=args.model_name)

    dst = pathlib.Path(args.dst).resolve()
    run_copier(dst, data, update=args.update)
    apply_memory_overlay(dst / "runtime" / "config.yaml", pathlib.Path(args.overlay))

    momo_agent_id = f"{slug}-momo"
    print(f"[adapter] export MOMO_AGENT_ID={momo_agent_id}  "
          f"(record-decision source=hermes://agent/{momo_agent_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
