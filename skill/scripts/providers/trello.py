#!/usr/bin/env python3
"""Momo's self-contained Trello board adapter (stdlib only — no uv/httpx).

This is the Trello twin of the pjangler `tp` adapter's providers/trello.sh, but
bundled INSIDE the momo skill so Momo carries its own board capability into ANY
repo — the repo needs only a `.project.json` (ticket_provider.type = "trello")
and, when its kanban columns are non-standard, a `.momo/config.json` lane map.
Nothing is installed per-repo; local parameters override shared behavior.

Implements the same normalized-op contract as `tp` so Momo's board-awareness
doctrine is provider-uniform:
    resolve                          -> {provider, board_id, board_url, me, list_map, board_lists}
    active_milestone                 -> {id, name, state}   (Trello has no cycles; board-as-milestone)
    list_issues                      -> [{id, key, title, state, state_type, list, url, ...}]
    get_issue <id|idShort>           -> {id, key, title, description, acceptance, state, list, comments}
    comment <id> <body>              -> prints comment id
    transition <id> <state|lane>     -> move to the lane for a normalized state, OR a literal lane name

Credentials (env): TRELLO_API_KEY (or TRELLO_KEY) + TRELLO_TOKEN.
Board id: --board-id, else $TRELLO_BOARD_ID, else .project.json ticket_provider.board_id.
Lane map: <root>/.momo/config.json  "lanes" table (multi-lane per state). Falls back to
the STANDARD flow if absent. Fails loud (never guesses) on an unmapped/unknown target.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

API = "https://api.trello.com/1"

# Normalized state -> Trello lane(s). Used when a repo has no .momo/config.json.
# Matches the pjangler trello.sh standard defaults. Non-standard boards supply a
# config; the FIRST lane per state is the canonical write target.
_STANDARD_LANES = {
    "backlog": ["Backlog"],
    "unstarted": ["To Do"],
    "started": ["In Progress"],
    "in_review": ["Review"],
    "completed": ["Done"],
}
_NORMALIZED_STATES = list(_STANDARD_LANES)


def die(msg: str, code: int = 2):
    sys.stderr.write(f"trello: {msg}\n")
    raise SystemExit(code)


def find_root(start: str) -> str:
    d = os.path.abspath(start)
    while True:
        if os.path.isfile(os.path.join(d, ".project.json")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.abspath(start)
        d = parent


def load_project(root: str) -> dict:
    path = os.path.join(root, ".project.json")
    try:
        return json.loads(open(path, encoding="utf-8").read())
    except Exception:
        return {}


def load_config(root: str) -> dict:
    path = os.path.join(root, ".momo", "config.json")
    if not os.path.isfile(path):
        return {}
    try:
        return json.loads(open(path, encoding="utf-8").read())
    except Exception as e:
        die(f"invalid .momo/config.json: {e}")


def lane_map(config: dict) -> dict:
    lanes = (config.get("lanes") or {}) if isinstance(config, dict) else {}
    m = {k: list(v) for k, v in _STANDARD_LANES.items()}
    for state in m:
        if isinstance(lanes.get(state), list) and lanes[state]:
            m[state] = list(lanes[state])
    return m


def write_target(config: dict, lm: dict, state: str) -> str:
    wt = (config.get("write_targets") or {}) if isinstance(config, dict) else {}
    return wt.get(state) or lm[state][0]


def state_for_lane(lane: str, lm: dict) -> str:
    folded = lane.casefold()
    for state in ("completed", "in_review", "started", "unstarted", "backlog"):
        if any(
            isinstance(candidate, str) and candidate.casefold() == folded
            for candidate in lm[state]
        ):
            return state
    return "other"


def resolve_target_list(lists: object, lane: object) -> dict:
    """Resolve one live lane without silently collapsing duplicate names."""
    if not isinstance(lane, str) or not lane:
        die(f"invalid configured target lane {lane!r}", 3)
    if not isinstance(lists, list):
        die("board lists response is not an array", 4)

    by_name: dict[str, dict] = {}
    for item in lists:
        if not isinstance(item, dict):
            die("board lists response contains a non-object", 4)
        list_id = item.get("id")
        name = item.get("name")
        if not isinstance(list_id, str) or not list_id:
            die("board lists response contains a list without an id", 4)
        if not isinstance(name, str) or not name:
            die(f"board list {list_id!r} has no name", 4)
        folded = name.casefold()
        if folded in by_name:
            prior = by_name[folded]
            die(
                "duplicate live lanes are ambiguous: "
                f"{prior['name']!r} ({prior['id']}) and {name!r} ({list_id})",
                3,
            )
        by_name[folded] = {"id": list_id, "name": name}

    resolved = by_name.get(lane.casefold())
    if resolved is None:
        live_names = sorted(item["name"] for item in by_name.values())
        die(
            f"target lane {lane!r} is not on the board. Lanes: {live_names}. "
            "Fix .momo/config.json — not guessing.",
            3,
        )
    return resolved


def validate_card(
    payload: object,
    *,
    stage: str,
    expected_id: str | None = None,
    expected_ref: str | None = None,
    expected_list: str | None = None,
) -> str:
    """Validate a Trello card response and return its canonical id."""
    if not isinstance(payload, dict):
        die(f"{stage} did not return a card object", 4)
    card_id = payload.get("id")
    if not isinstance(card_id, str) or not card_id:
        die(f"{stage} returned a card without an id", 4)
    if expected_id is not None and card_id != expected_id:
        die(
            f"{stage} returned different card {card_id!r}; expected {expected_id!r}",
            4,
        )
    if expected_ref is not None:
        identities = {
            str(value)
            for value in (
                payload.get("id"),
                payload.get("idShort"),
                payload.get("shortLink"),
            )
            if value is not None
        }
        if expected_ref not in identities:
            die(
                f"{stage} resolved {expected_ref!r} to a different card "
                f"{card_id!r}",
                4,
            )
    if expected_list is not None and payload.get("idList") != expected_list:
        die(
            f"{stage} returned list {payload.get('idList')!r}; "
            f"expected {expected_list!r}",
            4,
        )
    return card_id


def transition_card(
    trello: "Trello",
    board: str,
    card_ref: str,
    target: str,
    config: dict,
    lm: dict,
) -> dict:
    """Move one card once, then prove the exact card and list via live readback."""
    live_lists = trello.get(f"boards/{board}/lists", {"fields": "name"})
    if target in _NORMALIZED_STATES:
        configured_lane = write_target(config, lm, target)
    else:
        configured_lane = target
    target_list = resolve_target_list(live_lists, configured_lane)

    card_fields = {"fields": "id,idList,shortLink,idShort"}
    before = trello.get(f"cards/{card_ref}", card_fields)
    card_id = validate_card(
        before,
        stage="card lookup",
        expected_ref=card_ref,
    )

    updated = trello.put(f"cards/{card_id}", {"idList": target_list["id"]})
    validate_card(
        updated,
        stage="PUT response",
        expected_id=card_id,
        expected_list=target_list["id"],
    )

    readback = trello.get(f"cards/{card_id}", card_fields)
    validate_card(
        readback,
        stage="GET readback",
        expected_id=card_id,
        expected_list=target_list["id"],
    )

    lane = target_list["name"]
    return {
        "ok": True,
        "card": card_id,
        "requested_card": card_ref,
        "target": target,
        "moved_to": lane,
        "state": state_for_lane(lane, lm),
    }


class Trello:
    def __init__(self, key: str, token: str):
        self.key, self.token = key, token

    def _url(self, path: str, extra: dict | None = None) -> str:
        q = {"key": self.key, "token": self.token, **(extra or {})}
        return f"{API}/{path}?{urllib.parse.urlencode(q)}"

    def _req(self, method: str, path: str, extra: dict | None = None):
        req = urllib.request.Request(self._url(path, extra), method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            die(f"{method} {path} -> HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}", 4)
        except Exception as e:
            die(f"{method} {path} -> {e}", 4)
        return json.loads(body) if body.strip() else {}

    def get(self, path, extra=None):
        return self._req("GET", path, extra)

    def put(self, path, extra=None):
        return self._req("PUT", path, extra)

    def post(self, path, extra=None):
        return self._req("POST", path, extra)


def creds() -> tuple[str, str]:
    key = os.environ.get("TRELLO_API_KEY") or os.environ.get("TRELLO_KEY")
    token = os.environ.get("TRELLO_TOKEN")
    if not key or not token:
        die("TRELLO_API_KEY (or TRELLO_KEY) and TRELLO_TOKEN must be set", 2)
    return key, token


def emit(obj):
    print(json.dumps(obj, indent=2))


def main() -> int:
    argv = sys.argv[1:]
    root = os.getcwd()
    board_override = None
    # Pull out --root / --board-id anywhere in argv.
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--root" and i + 1 < len(argv):
            root = argv[i + 1]; i += 2; continue
        if argv[i] == "--board-id" and i + 1 < len(argv):
            board_override = argv[i + 1]; i += 2; continue
        rest.append(argv[i]); i += 1
    if not rest:
        sys.stderr.write(__doc__ or "")
        return 2

    root = find_root(root)
    project = load_project(root)
    config = load_config(root)
    lm = lane_map(config)
    tp = (project.get("ticket_provider") or {}) if isinstance(project, dict) else {}
    board = board_override or os.environ.get("TRELLO_BOARD_ID") or tp.get("board_id")
    if not board:
        die("no board id (--board-id, $TRELLO_BOARD_ID, or .project.json ticket_provider.board_id)", 2)

    key, token = creds()
    t = Trello(key, token)
    op, args = rest[0], rest[1:]

    if op == "resolve":
        b = t.get(f"boards/{board}", {"fields": "name,url"})
        me = t.get("members/me", {"fields": "username,fullName"})
        lists = t.get(f"boards/{board}/lists", {"fields": "name"})
        emit({
            "provider": "trello",
            "board_id": b.get("id", board),
            "board_url": b.get("url", ""),
            "board_name": b.get("name", ""),
            "me": {"id": me.get("id", ""), "username": me.get("username", ""), "full_name": me.get("fullName", "")},
            "list_map": lm,
            "config_present": bool(config),
            "board_lists": [l.get("name", "") for l in lists],
        })
    elif op == "active_milestone":
        b = t.get(f"boards/{board}", {"fields": "name"})
        emit({"id": b.get("id", board), "name": b.get("name", ""), "state": "active"})
    elif op == "list_issues":
        lists = {l["id"]: l.get("name", "") for l in t.get(f"boards/{board}/lists", {"fields": "name"})}
        cards = t.get(f"boards/{board}/cards", {"fields": "name,idList,dateLastActivity,url,shortLink,idMembers"})
        rows = []
        for c in cards:
            lane = lists.get(c.get("idList", ""), "?")
            state = state_for_lane(lane, lm)
            rows.append({
                "id": c.get("id", ""), "key": c.get("shortLink", ""), "title": c.get("name", ""),
                "state": state, "state_type": state, "list": lane,
                "updated_at": c.get("dateLastActivity", ""), "assignee": c.get("idMembers", []),
                "url": c.get("url", ""),
            })
        order = {"started": 0, "in_review": 1, "unstarted": 2, "backlog": 3, "completed": 4, "other": 5}
        rows.sort(key=lambda r: (order.get(r["state"], 9), r["list"], r["title"]))
        emit(rows)
    elif op == "get_issue":
        if not args:
            die("get_issue needs <id|idShort>")
        c = t.get(f"cards/{args[0]}", {"fields": "name,desc,idList,shortLink,url,idShort"})
        lists = {l["id"]: l.get("name", "") for l in t.get(f"boards/{board}/lists", {"fields": "name"})}
        lane = lists.get(c.get("idList", ""), "?")
        acts = t.get(f"cards/{args[0]}/actions", {"filter": "commentCard", "limit": "50"})
        emit({
            "id": c.get("id", ""), "key": c.get("shortLink", ""), "title": c.get("name", ""),
            "description": c.get("desc", ""), "acceptance": c.get("desc", ""),
            "state": state_for_lane(lane, lm), "state_type": state_for_lane(lane, lm), "list": lane,
            "url": c.get("url", ""),
            "comments": [
                {"id": a.get("id", ""), "author": (a.get("memberCreator") or {}).get("username", ""),
                 "date": a.get("date", ""), "body": (a.get("data") or {}).get("text", "")}
                for a in acts
            ],
        })
    elif op == "comment":
        if len(args) < 2:
            die("comment needs <id|idShort> <body>")
        res = t.post(f"cards/{args[0]}/actions/comments", {"text": " ".join(args[1:])})
        print(res.get("id", ""))
    elif op == "transition":
        if len(args) < 2:
            die("transition needs <id|idShort> <state|lane>")
        card_ref, target = args[0], args[1]
        emit(transition_card(t, board, card_ref, target, config, lm))
    else:
        die(f"unknown op {op!r}. Ops: resolve|active_milestone|list_issues|get_issue|comment|transition")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
