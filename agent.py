"""SubSentinel — an Everyday Agent built with the Strands Agents SDK.

Reads an inbox, detects recurring charges / subscriptions, keeps a persistent
memory of known subscriptions across runs, flags price hikes, and drafts
cancellation or negotiation emails the user can send with one click.

Model backend is OpenAI-compatible (works with OpenRouter, OpenAI, or any
compatible gateway) configured via environment variables:

    LLM_BASE_URL   e.g. https://openrouter.ai/api/v1
    LLM_API_KEY    your API key
    LLM_MODEL      e.g. nvidia/nemotron-3-super-120b-a12b:free

Run:
    python agent.py            # one audit run against the demo mailbox
    python agent.py --interactive
"""

import argparse
import json
import os
from datetime import datetime, timezone

from strands import Agent, tool
from strands.models.openai import OpenAIModel
from openai import AsyncOpenAI

from tools.mailbox import fetch_recent_emails
from tools.persist import (
    load_subscriptions,
    save_subscriptions,
    diff_against_memory,
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DRAFTS_PATH = os.path.join(DATA_DIR, "drafted_emails.json")
AUDIT_PATH = os.path.join(DATA_DIR, "last_audit.json")


# ---------------------------------------------------------------- tools ----

@tool
def read_inbox(folder: str = "inbox", limit: int = 50) -> str:
    """Read recent emails from the mailbox (folder=inbox|receipts). Returns JSON."""
    emails = fetch_recent_emails(folder=folder, limit=limit)
    return json.dumps({"count": len(emails), "emails": emails}, indent=2)


@tool
def remember_subscriptions(subscriptions: list[dict]) -> str:
    """Persist the current picture of the user's subscriptions.

    Each item: {name, merchant, amount, currency, cadence, last_charge_date,
                first_seen, status(active|cancelled), notes}
    """
    save_subscriptions(subscriptions)
    return f"Saved {len(subscriptions)} subscriptions to memory."


@tool
def recall_subscriptions() -> str:
    """Load the subscriptions remembered from previous audit runs."""
    return json.dumps(load_subscriptions(), indent=2)


@tool
def compare_with_memory(current: list[dict]) -> str:
    """Diff the subscriptions found in this run against persistent memory.

    Returns new subscriptions, price hikes, and cancellations.
    """
    return json.dumps(diff_against_memory(current), indent=2)


@tool
def save_email_draft(to: str, subject: str, body: str, kind: str = "cancellation") -> str:
    """Save a drafted email (cancellation / negotiation / refund) for user review."""
    drafts = []
    if os.path.exists(DRAFTS_PATH):
        with open(DRAFTS_PATH) as f:
            drafts = json.load(f)
    drafts.append({
        "to": to,
        "subject": subject,
        "body": body,
        "kind": kind,
        "drafted_at": datetime.now(timezone.utc).isoformat(),
    })
    with open(DRAFTS_PATH, "w") as f:
        json.dump(drafts, f, indent=2)
    return f"Draft saved ({len(drafts)} total)."


@tool
def save_audit_report(report: str) -> str:
    """Save the final human-readable audit report."""
    with open(AUDIT_PATH, "w") as f:
        f.write(report)
    return "Audit report saved to data/last_audit.json"


# ---------------------------------------------------------------- agent ----

SYSTEM_PROMPT = """You are SubSentinel, an everyday agent that stops subscription leaks.

Your job in a single audit run:
1. read_inbox to collect recent emails (receipts, price-change notices, renewals).
2. Identify recurring charges and subscriptions: name, merchant, amount, cadence, last charge date.
3. recall_subscriptions to load what you knew from previous runs, then compare_with_memory
   to surface: NEW subscriptions, PRICE HIKES (>5%), and things that look CANCELLED.
4. For every problem found (new forgotten trial, price hike, unused-looking subscription),
   use save_email_draft to draft either:
     - a polite cancellation email, or
     - a negotiation email asking for a discount or loyalty rate, or
     - a refund request if the user was charged after cancelling.
5. remember_subscriptions with the updated full picture so the next run is smarter.
6. save_audit_report with a short markdown report for the user:
   - total estimated monthly spend, changes vs last run, and the drafts you prepared.

Tone: concise, concrete, numbers-first. Never invent charges that are not in the emails.
If the mailbox is empty, say so and save an empty-state report.
"""


def build_agent() -> Agent:
    base_url = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    api_key = os.environ.get("LLM_API_KEY")
    model_id = os.environ.get("LLM_MODEL", "nvidia/nemotron-3-super-120b-a12b:free")
    if not api_key:
        raise SystemExit("Set LLM_API_KEY (and optionally LLM_BASE_URL / LLM_MODEL).")

    client = AsyncOpenAI(base_url=base_url, api_key=api_key)
    model = OpenAIModel(client=client, model_id=model_id)

    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            read_inbox,
            remember_subscriptions,
            recall_subscriptions,
            compare_with_memory,
            save_email_draft,
            save_audit_report,
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="SubSentinel audit run")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    agent = build_agent()
    kickoff = (
        "Run a full subscription audit now. Start with read_inbox. "
        "When you finish, tell me the 3 most important findings."
        if not args.interactive
        else "Interactive mode. Ask me anything about my subscriptions."
    )
    result = agent(kickoff)
    print(result)


if __name__ == "__main__":
    main()
