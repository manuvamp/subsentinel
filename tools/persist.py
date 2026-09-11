"""Persistent subscription memory (JSON file store).

Swap for DynamoDB/SQLite in production — the agent-facing API stays identical.
"""

import json
import os

HERE = os.path.dirname(__file__)
STORE = os.path.join(HERE, "..", "data", "subscriptions.json")


def load_subscriptions() -> list[dict]:
    if not os.path.exists(STORE):
        return []
    with open(STORE) as f:
        return json.load(f)


def save_subscriptions(subs: list[dict]) -> None:
    with open(STORE, "w") as f:
        json.dump(subs, f, indent=2)


def _match(a: dict, b: dict) -> bool:
    return a.get("name", "").lower() == b.get("name", "").lower()


def diff_against_memory(current: list[dict]) -> dict:
    known = load_subscriptions()
    known_map = {k.get("name", "").lower(): k for k in known}

    new, hikes, cancelled = [], [], []
    for c in current:
        k = known_map.get(c.get("name", "").lower())
        if not k:
            new.append(c)
            continue
        try:
            if float(c.get("amount", 0)) > float(k.get("amount", 0)) * 1.05:
                hikes.append({
                    "name": c.get("name"),
                    "was": k.get("amount"),
                    "now": c.get("amount"),
                })
        except (TypeError, ValueError):
            pass
    for k in known:
        if not any(_match(c, k) for c in current):
            cancelled.append(k)

    return {"new": new, "price_hikes": hikes, "possibly_cancelled": cancelled}
