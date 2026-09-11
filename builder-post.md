# Building SubSentinel: an Everyday Agent that stops subscription leaks with the Strands Agents SDK

*Submission for the Agents for Humans Hackathon — Everyday Agents track*

## The problem

The average household leaks hundreds of dollars a year on subscriptions it forgot about: free trials that quietly convert, "new pricing" emails nobody opens, charges that continue after a cancellation. Detecting leaks by hand means reading receipts and price-change notices every month. That's an everyday problem an everyday agent should own.

## The agent

SubSentinel runs a full audit in one command (`python agent.py`):

1. **read_inbox** — parses receipts, renewals, trial notices and price-change emails
2. **recall_subscriptions** — loads the subscription picture it memorized on previous runs
3. **compare_with_memory** — surfaces NEW subscriptions, PRICE HIKES (>5%), and apparent cancellations
4. **save_email_draft** — writes the reply: a cancellation, a loyalty-discount negotiation, or a refund request
5. **remember_subscriptions** — stores the updated picture so the next run is smarter
6. **save_audit_report** — a markdown report with estimated monthly spend and every change

The differentiator is agent memory across runs: run it monthly and it reasons about *change*, which is exactly where the money leaks.

## What the Strands Agents SDK gave us

- **The tool-use loop for free.** Six tools, no glue code: the model chains them autonomously, including the memory diff and the drafting step.
- **A portable model layer.** `OpenAIModel` with any OpenAI-compatible endpoint — our demo runs on a free tool-calling model via OpenRouter, so the whole project costs $0 to run.
- **Deterministic, testable runs.** The seeded demo inbox ships in-repo; anyone can reproduce the exact audit without credentials.

## Things we learned

- Strands' async event loop expects an `AsyncOpenAI` client — a one-line fix that cost us a traceback.
- The hard part of an everyday agent isn't the model, it's giving it a truthful, persistent picture of the user's world. Memory-first design turned a stateless summarizer into an auditor.
- Honesty constraints belong in the system prompt: SubSentinel may never invent charges that aren't in the emails.

## What's next

- Gmail API adapter (the seeded shape is already the adapter's return shape)
- Weekly digest scheduling and a one-click send dashboard
- Negotiation follow-up tracking

**Repo:** https://github.com/manuvamp/subsentinel — MIT licensed, demo reproduces in minutes.
