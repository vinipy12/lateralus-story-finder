# Lateralus Story Finder

> **Status: in progress — slice 1 (the bot answers `/start`); the briefing pipeline
> is designed but not built yet.** Today the bot replies to its owner's `/start`
> and nothing else. Gathering, summarizing and scheduling exist only as the design
> documents and the summarizer eval described below.

A personal Telegram bot that follows a handful of Reddit communities and briefs
their best threads of the week in Brazilian Portuguese.

It is single-user by design. One person registers the communities, one person
receives the briefs, and nothing is published, shared, or redistributed.

## What it is meant to do

You register subreddits with the bot. Once a week it gathers each one's
highest-traction posts and sends a short index in Portuguese — translated titles
with a link to each original thread. Tapping an entry summarizes that post's
discussion and body into Portuguese and replies with it.

Summaries are produced only when you open a post, so the running cost tracks what
you actually read rather than everything that was gathered.

**Read-only.** The bot never posts, comments, votes, messages, subscribes, or
moderates. Every brief links back to the original thread rather than replacing it.

## Status

Early. Built in small vertical slices, each specified before it is written.

| Slice | State |
|---|---|
| Owner-locked bot that answers `/start` in pt-BR | done |
| Subscriptions — register, list, remove communities | in progress (not yet wired; `/start` already lists the planned commands) |
| Weekly gathering and on-demand briefs | specified, not started |
| Scheduling | specified, not started |

Open work is tracked as [issues](https://github.com/vinipy12/lateralus-story-finder/issues).

## Design

The design is written down before the code is, and the reasoning behind the
non-obvious decisions is recorded rather than left to be rediscovered:

- [Design specification](docs/superpowers/specs/2026-08-20-story-finder-design.md)
- [Domain glossary](CONTEXT.md) — authoritative for the terms used throughout
- Architecture decisions:
  - [Catch-up-on-wake scheduling](docs/adr/0001-catch-up-on-wake-scheduling.md)
  - [Discussion as primary content](docs/adr/0002-discussion-as-primary-content.md)
  - [Local-first inference behind a seam](docs/adr/0003-local-first-inference-behind-a-seam.md)
  - [RSS is the permanent Reddit source](docs/adr/0005-rss-is-the-permanent-source.md)

## Summarizer eval

[`evals/`](evals/) holds the harness used to choose the model behind the
summarizer: a shared prompt ([`PROMPT.md`](evals/PROMPT.md)), a scoring rubric
([`RUBRIC.md`](evals/RUBRIC.md)), one runner per provider (`run_anthropic.py`,
`run_openai.py`, `run_codex.py`, `run_ollama.py`) and the written results and judge
verdicts. The real Reddit threads it was run against are not published; the
fixtures directory holds three synthetic threads that show the input format (see
[`evals/fixtures/MANIFEST.md`](evals/fixtures/MANIFEST.md)). The API runners need
the optional `evals` extra: `pip install -e ".[evals]"`.

## Reading Reddit

Reddit closed self-service API access in November 2025, and this project's access
request was refused in August 2026. It reads **public RSS feeds instead** — no
account, no app registration, no credentials.

The cost of that is fixed and known: no scores or comment counts (the index shows
rank instead), no comment threading, and private, quarantined and banned
communities are indistinguishable from each other. Quarantined communities cannot
be read at all.

## Running it

Requires Docker and a Telegram bot token. Reddit needs no credentials.

```sh
./scripts/setup-credentials.sh   # walks you through the Telegram setup
docker compose up --build
```

The setup wizard opens each page you need, says exactly what to click, and writes
the values to a git-ignored `.env`. The bot answers a single Telegram user ID and
ignores everyone else.

It uses long-polling rather than webhooks, so it needs no public endpoint and runs
behind a home connection unchanged.

### Tests

```sh
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

Tests that touch a live external API are marked `contract` and excluded by default,
so the suite stays offline and deterministic.

### Repository integrity

```sh
python3 scripts/check_repo_integrity.py
```

The repository identity is committed in
[`.lateralus/project.json`](.lateralus/project.json). Harness operations must treat
a missing or malformed identity file as a hard error; they must not infer identity
from a checkout path, repository basename, or another project's defaults.

## License

See [LICENSE](LICENSE).
