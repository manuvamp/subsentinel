"""Synthetic + real mailbox access.

The demo ships with a seeded mailbox (JSON) so the agent is fully runnable
without credentials. For production use, implement fetch_recent_emails with an
IMAP/Gmail-API backend behind the same return shape.
"""

import json
import os

HERE = os.path.dirname(__file__)
SEED_PATH = os.path.join(HERE, "..", "data", "seed_inbox.json")


def fetch_recent_emails(folder: str = "inbox", limit: int = 50) -> list[dict]:
    with open(SEED_PATH) as f:
        box = json.load(f)
    emails = box.get(folder, [])
    emails.sort(key=lambda e: e.get("date", ""), reverse=True)
    return emails[:limit]
