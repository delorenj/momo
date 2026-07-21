# record-decision.py — reconcile source/producer to the fleet URI scheme

Target: `~/code/33GOD/momo/skill/scripts/record-decision.py`
(byte-identical twin at `~/code/33GOD/skills/momo/scripts/record-decision.py` —
patch both, or dedup first).

## The divergence

| field | current (record-decision.py) | fleet scheme (role.yaml.jinja / SOUL.md.jinja) |
| --- | --- | --- |
| `source`   | `urn:33god:agent:<actor>:<slug>` (L123) | `hermes://agent/<agent_id>` (SOUL.md.jinja:47) |
| `producer` | `agent:<actor>` (L130)                  | `hermes-agent:<agent_id>` (role.yaml.jinja:65) |
| `actor.agent_id` | `<actor>` (= "momo") (L132)       | `<agent_id>` (SOUL.md.jinja:45) |

`<agent_id>` in the fleet is `<repo>-<role>`. Momo is the human-drivable **twin**
of `<repo>-pm`, so it gets a DISTINCT fleet identity `<repo>-momo` (never
`<repo>-pm` — masquerading as Hermes would break attributability /
`one-source-of-truth`).

## Contract preservation

The momo skill contract ("sign decisions as **momo**") is preserved by keeping
`data.decided_by = "momo"` and by the `-momo` suffix in the agent_id. Only the
envelope-level carrier identity (source/producer/actor.agent_id) moves to the
fleet scheme. `decisions.md` line that reads `actor.agent_id=momo` updates to
`actor.agent_id=<repo>-momo, decided_by=momo`.

## Schema safety (verified)

`_common/cloudevent_base.v1.json`: `source` is `format: uri-reference` (minLength 1)
— `hermes://agent/holocene-momo` is a valid uri-reference. `producer` is a free
string. So this is a pure convention reconciliation, NOT a schema change; the
existing `repo/decision.recorded.v1.json` still validates.

## Patch

```diff
@@ after slug is resolved (~L106) @@
     if not slug:
         print("record-decision: could not resolve repo slug from .project.json", file=sys.stderr)
         return 2
+
+    # Momo's DISTINCT fleet identity — twin of <repo>-pm. Feeds the envelope
+    # carrier fields (source/producer/actor) so they match the on-disk fleet
+    # scheme (hermes://agent/<agent_id>, hermes-agent:<agent_id>). The stable
+    # human-facing signature stays in data.decided_by (= actor, default "momo").
+    agent_id = os.environ.get("MOMO_AGENT_ID") or (
+        args.actor if "-" in args.actor else f"{slug}-{args.actor}"
+    )

@@ env = { ... } (~L120) @@
-        "source": f"urn:33god:agent:{args.actor}:{slug}",
+        "source": f"hermes://agent/{agent_id}",
         "type": CE_TYPE,
         "subject": NATS_SUBJECT,
         "time": now_iso(),
         "datacontenttype": "application/json",
         "kind": "event",
         "domain": "repo",
-        "producer": f"agent:{args.actor}",
+        "producer": f"hermes-agent:{agent_id}",
         "service": slug,
-        "actor": {"type": "agent_cli", "agent_id": args.actor, "cli": args.cli, "provider": args.provider},
+        "actor": {"type": "agent_cli", "agent_id": agent_id, "cli": args.cli, "provider": args.provider},
```

Add the optional flag (near the other `ap.add_argument` calls):

```python
ap.add_argument("--agent-id", dest="agent_id_override",
                default=os.environ.get("MOMO_AGENT_ID"),
                help="fleet agent_id for envelope carrier fields "
                     "(default: <repo_slug>-<actor>, e.g. holocene-momo)")
```

…and prefer it in the resolution: `agent_id = args.agent_id_override or (...)`.

`data.decided_by` (L114) stays `args.actor` (= "momo") — unchanged.

## Adapter linkage

The adapter exports `MOMO_AGENT_ID=<repo_slug>-momo` into the environment Momo /
the Hermes twin runs under (systemd unit `Environment=` or the runtime `.env`),
so every decision event self-attributes to the twin without a per-call flag.
