# Lateralus Story Finder — Design

**Date:** 2026-08-20
**Status:** Approved for implementation
**Vocabulary:** [`CONTEXT.md`](../../../CONTEXT.md) is authoritative for domain terms.

## Problem

Following several subreddits means either checking Reddit habitually or missing the
week's good threads. Reading them in English adds friction on top.

Story Finder removes both. It is a single-Owner Telegram bot that tracks a set of
subreddits, gathers each one's highest-Traction posts once a week, and briefs them
in Brazilian Portuguese.

## Product shape

The Owner registers Subscriptions. Once a week a Digest gathers each Subscription's
top posts and sends an Index in pt-BR: numbered entries with translated titles and
their standing for the week. Tapping an entry produces a Brief — that post's
Discussion, and its body when it has one — translated and summarized.

Briefs are produced **lazily**, on tap. Only opened posts cost tokens or GPU time,
so running cost tracks what is actually read rather than what is gathered.

### Traction

Traction is Reddit's own `top?t=week` ordering — a post's *rank* within the week,
not a number. Reddit's ranking already accounts for subreddit size, so there is no
scoring logic to own, and no scoring logic is possible: the Atom feeds this project
reads carry no score and no comment count. Ordering is the entire signal. See
[ADR-0005](../../adr/0005-rss-is-the-permanent-source.md).

### Discussion is the primary content

A Brief's principal content is the post's Discussion. The post body is optional
enrichment, absent entirely on link and image posts — which make up a large share
of top-of-week material, and whose linked articles this project does not fetch.

Treating the body as primary would leave those posts with empty Briefs. Treating
Discussion as primary is also truer to Reddit: on an image post, the thread *is*
the substance. See [ADR-0002](../../adr/0002-discussion-as-primary-content.md).

### A post is briefed once, ever

Top-of-week rankings overlap heavily between runs. A post carried by any earlier
Digest is never carried again, whatever its current Traction.

To keep an Index full rather than letting it thin out, each Digest fetches deeper
than it displays — `DIGEST_FETCH_DEPTH` posts — discards everything already carried,
and takes the first `DIGEST_POSTS_PER_SUB` survivors. One feed request returns the
whole depth, so fetching deeper costs no extra requests.

**The feeds honour `limit` up to 100.** Probed 2026-08-21: `r/AskReddit` returned
exactly 100 entries at `limit=100`. Smaller results elsewhere the same day —
`r/UnresolvedMysteries` 16, `r/LetsNotMeet` 9, `r/TrueCrime` 1 — are those
subreddits' actual weekly volume, not a page cap. So `DIGEST_FETCH_DEPTH` has real
headroom on busy subreddits, and on quiet ones the constraint is that the week
genuinely contains few posts, which no amount of fetching fixes.

### Language

All Owner-facing copy is Brazilian Portuguese — greetings, help, Indexes, Briefs,
and errors alike. Logs remain in English. Posts already in Portuguese are
summarized without a translation step.

## Runtime

A single long-running Python process in a Docker container, initially on the
Owner's laptop.

**Long-polling, not webhooks.** A webhook needs a public HTTPS endpoint, which a
machine behind home NAT lacks. Long-polling behaves identically local or hosted, so
the same container moves to a cheap VPS later unchanged.

State is a SQLite file on a mounted volume — migrating hosts is copying one file.

### Scheduling: catch-up-on-wake

The host is a laptop. It sleeps, closes, and travels, so wall-clock scheduling would
silently skip weeks with no message and no error.

Instead: on startup and on an hourly tick, run a Digest if more than
`DIGEST_INTERVAL_DAYS` have elapsed since the last one **and** local time falls
within the send window. The Digest arrives late rather than never, the container is
restart-safe for free, and the send window prevents a 3 a.m. notification when the
laptop wakes. See [ADR-0001](../../adr/0001-catch-up-on-wake-scheduling.md).

## Architecture

Five modules, each with one responsibility and a narrow interface.

| Module | Responsibility |
|---|---|
| `bot` | Telegram handlers and callback routing. Knows nothing of Reddit or LLMs; calls the layers below and formats replies. |
| `reddit` | The only module that talks to Reddit. Validates a subreddit is readable; fetches top-of-week posts; selects Discussion; paces requests. Parses Atom and returns domain objects — no feed structure escapes it. |
| `digest` | Runs a Digest: for each Subscription fetch, dedupe, persist, then compose the Index. Pure orchestration. |
| `summarizer` | One interface: given a post and its Discussion, return a pt-BR Brief. Implementation is swappable. |
| `store` | SQLite persistence. |

### The summarizer seam

The project starts on a **local model via Ollama** — zero marginal cost, no API key,
free to iterate against.

The constraint is hardware: a 4GB RTX 3050 caps the practical model at roughly 4B
parameters. `qwen3.5:4b` is strong multilingually for its size, but pt-BR idiom and
sarcastic threads are exactly where small models are weakest. That is an open
question, not a settled one.

So `summarizer` is a single narrow interface, and the choice gets a **quality gate**
rather than an indefinite maybe: when the Brief path ships, ten real threads run
through both the local model and Opus 5, compared side by side, before committing.
Opus 5 is the reference deliberately — comparing against a mid-tier model would
leave a good local result indistinguishable from a weak reference.
See [ADR-0003](../../adr/0003-local-first-inference-behind-a-seam.md).

A ChatGPT/Codex subscription was considered and does not apply: those credits work
only inside Codex and ChatGPT for Excel, not for an API key called programmatically.

### Discussion selection

Selection is deterministic code in `reddit`, not the model's job — the same thread
yields the same input regardless of which model sits behind the seam.

Take the first `DISCUSSION_TOP_COMMENTS` entries from the post's comment feed,
capped at `DISCUSSION_CHAR_BUDGET` characters total. Drop `[deleted]`, `[removed]`,
and AutoModerator.

**"First N", not "top N by score", and not threaded.** The feed carries no
per-comment score and no parent-child structure, so selection follows Reddit's own
comment ordering flat. This approximates "the comments Reddit thinks matter" without
being able to verify it, and it is the permanent strategy rather than a stand-in —
see [ADR-0005](../../adr/0005-rss-is-the-permanent-source.md). It is also the single
largest known quality risk in the design, which is why the eval harness ships with
the Brief path rather than after it.

These are configuration, not constants. Finding good values is expected to take
iteration, and the eval harness exists to make that iteration cheap.

### Eval harness

Tuning Discussion selection and settling the model choice are the same activity:
run the same threads through different configurations and compare. Done by hand —
re-tapping posts in Telegram, scrolling to compare — it stops happening after a day.

So the Brief slice ships a small harness: ~10 real threads saved as fixtures, and a
script that runs them through any configured summarizer and writes the outputs side
by side. Fixtures make comparisons reproducible and offline — no Reddit calls, no
rate limits, identical input every run.

## Data model

Domain objects are Pydantic models. Pydantic is used in three places: domain
objects, configuration (`pydantic-settings`), and validated parsing at both external
boundaries — Reddit feeds and model output. Nothing untyped crosses a seam.

    Subscription    subreddit, added_at
    RedditPost      id, subreddit, rank, title, author, permalink, url,
                    created_utc, selftext, is_self
    Comment         id, author, body
    Brief           post_id, title_pt, content_pt?, discussion_pt,
                    generated_at, model_id, tuning_fingerprint

`content_pt` is nullable — absent for link and image posts, where Discussion is the
only content. `rank` is the post's position in the week's feed, 1-based; it is the
only Traction figure that exists.

**There is no `score`, `num_comments`, `Comment.score`, or `Comment.depth`.** An
earlier revision carried them against the arrival of Reddit API credentials. That
access was refused ([ADR-0005](../../adr/0005-rss-is-the-permanent-source.md)) and
no source will ever populate them, so they are gone rather than nullable — a field
nothing fills is a schema that lies to the next reader.

`reddit` parses Atom into these models, so no feed structure escapes that module.
`summarizer` returns a validated `Brief`, so a local model emitting malformed or
half-English output fails loudly at the boundary rather than silently reaching the
chat. That matters more than usual given the model tier.

### Tables

| Table | Purpose | Arrives in |
|---|---|---|
| `subscriptions` | Registered subreddits | Slice 1 |
| `digests` | One row per run: `ran_at`, status. `last_digest_at` is `max(ran_at)` | Slice 2 |
| `digest_posts` | Posts a Digest carried. Backs both dedup and Index tap resolution | Slice 2 |
| `briefs` | Cache, keyed by post + model + tuning fingerprint | Slice 2 |

**No retention policy.** Five posts × five Subscriptions × 52 weeks is ~1,300 rows a
year; an expiry rule would buy nothing and break old taps.

**`digest_posts` does not cascade from `subscriptions`.** It stores the subreddit
name denormalized and outlives the Subscription. Removing a Subscription stops
future Digests from including it; it does not rewrite history, so taps on old
Indexes keep resolving.

**Brief cache key is `(post_id, model_id, tuning_fingerprint)`**, where the
fingerprint hashes the Discussion selection parameters. Change a setting and Briefs
regenerate automatically; earlier ones remain under their old fingerprint, so
settings can be diffed against the same post. Without this, tuning would silently
serve stale output built from different input — the failure mode that makes tuning
loops waste weeks.

## Reddit access

**The project reads public Atom feeds, unauthenticated. There is no API path.**

Reddit closed self-service Data API access on 2025-11-14 under its Responsible
Builder Policy. An access request was submitted 2026-08-20 and **refused on
2026-08-21** with no specific defect named and no appeal offered. The undocumented
`.json` endpoints return 403 from a residential connection. Public Atom feeds return
200 and are the only remaining source. See
[ADR-0005](../../adr/0005-rss-is-the-permanent-source.md).

`reddit` remains the only module that touches Reddit — not because a second adapter
is coming, but because feed-parsing has no business leaking into `digest` or `bot`.

**What the feeds carry, and what they do not:**

| Capability | Available | Consequence |
|---|---|---|
| Top-of-week ordering | yes | this is the whole Traction signal |
| Post title, author, permalink, body | yes | enough to build a Brief |
| Score and comment count | **no** | Index shows rank — "1º da semana" — never figures |
| Per-comment score | **no** | Discussion takes the first N feed entries, flat |
| Comment threading | **no** | no reply nesting; there is no depth setting |
| Distinct failure reasons | partial | see below |

**Failure reasons are inferred from HTTP status, not from an error payload.** Probed
live on 2026-08-21: a nonexistent subreddit returns **404** — with a well-formed but
empty Atom body, so status is the signal and body shape is not. A private subreddit
returns **403**. Rate limiting returns **429**. Cases the status cannot separate
collapse to a single "unreachable" message rather than guessing; the exact taxonomy
is settled by live probe in slice 1 (issue #3) rather than assumed here.

**Rate limiting is a design constraint, not a testing nuisance.** Probing on
2026-08-21 from a residential connection returned 429 even at one request every 35
seconds once a short burst had been spent — far harsher than the "one per 8 seconds"
earlier testing suggested, and nowhere near the ~100/minute the API tier would have
given. Consequences:

- `reddit` owns pacing and 429 backoff internally. Callers do not schedule requests.
- A weekly Digest is one request per Subscription — nine on the intended set — and is
  never the problem. `/add` validation is Owner-triggered and can burst, so it must
  tolerate a 429 by retrying rather than reporting the subreddit unreachable.
- The contract test and any live probing run deliberately slowly. The default suite
  stays offline.

## Subscriptions worth having

25 subreddits were probed anonymously on 2026-08-21 (issue #3). 24 returned 200 and
one returned 403.

**The NSFW flag alone does not block anonymous feed reads.** A deliberately
over-18-flagged, non-quarantined control subreddit returned a full feed. Only
*quarantine, private and banned* — the three that share a 403 — are barred, so NSFW
needs no branch anywhere in the code. This had been the largest open question in the
design.

**Quarantine is not a broad risk either.** 24 of 25 came back 200. `r/MorbidReality`
is the exception: quarantined, and therefore permanently unreadable, because
quarantine requires a logged-in opted-in user and there are no credentials. It leaves
the intended set as a scope fact rather than a bug.

### Select on self-post ratio, not size

The probe surfaced a trap worth writing down. `r/crime` has roughly a million
subscribers and produced **82 top posts in the week** — the highest volume in the
whole set — and is unusable: 6% self-posts, median self-text length **zero**. It is a
headline link aggregator, and this project does not fetch linked articles.
`r/MissingPersons` is the same shape: 25 posts, 0% self-posts, all flyers.
`r/TrueCrimeDiscussion` produced 20 posts, 100% self-posts, median ~1,450 characters.

So a Subscription's worth is **percentage of self-posts**. Not subscriber count, not
weekly volume — selecting on either reproduces exactly the `r/TrueCrime` result, a
large community that yielded one top post that week.

### The intended set

| Subreddit | Theme | Posts/wk | Self-post | Carries |
|---|---|---|---|---|
| `r/Paranormal` | paranormal | 100¹ | 88% | First-person accounts and discussion prompts |
| `r/Ghoststories` | paranormal | 100¹ | 92% | Long narrative encounters, almost no image noise |
| `r/HighStrangeness` | mystery | 76 | 70% | Anomalies and fringe science; argumentative, reply-heavy |
| `r/gratefuldoe` | unsolved | 54 | 80% | Doe identification and collaborative case work |
| `r/UnsolvedMysteries` | unsolved | 24 | 71% | Case discussion; distinct from `r/UnresolvedMysteries` |
| `r/UnresolvedMysteries` | unsolved | 16 | — | The original pick; confirmed readable |
| `r/TrueCrimeDiscussion` | true crime | 20 | 100% | Long-form write-ups and trial megathreads |
| `r/SerialKillers` | true crime | 16 | 69% | Short posts, but nearly all are questions |
| `r/LetsNotMeet` | true crime | 9 | — | The original pick; confirmed readable |

¹ Exactly 100 is the `limit` cap — a censored count, not a measurement. True weekly
volume for those two is unknown and higher.

Dropped from the original five: **`r/MorbidReality`** (unreadable) and
**`r/TrueCrime`** (one top post that week; `r/TrueCrimeDiscussion` replaces it).

Held in reserve, all confirmed readable but thinner: `r/Thetruthishere`, `r/Ghosts`,
`r/Glitch_in_the_Matrix`, `r/coldcases`, `r/RBI`.

**Subscribe broadly first, prune later.** Self-text length is a *proxy* for Discussion
depth, not a measurement of it — comment counts do not exist over RSS. Whether
`r/SerialKillers`' short question-posts out-discuss `r/Ghoststories`' long narratives
is genuinely unknown, and no amount of further probing settles it. Real Briefs do,
which is an argument for carrying more Subscriptions than feels necessary through the
first few Digests and cutting the ones that read thin.

**Retry-on-429 is load-bearing, and this is where it was proven.** Probing at
50-second spacing still drew 429 on 3 of 20 requests (15%), all 200 on retry. Two of
the three were `r/Ghoststories` and `r/HighStrangeness` — the second and third
entries in the table above. Without the retry rule in Failure behavior they would
have been recorded as unreachable and never appeared here at all.

## External dependencies

**Reddit** — public Atom feeds over plain HTTPS. **No account, no app registration,
no credentials, no PRAW.** A descriptive `User-Agent` is still sent: generic or
absent agents are rate-limited harder.

Unauthenticated access reaches public communities only. Private and banned
communities are unreadable by definition, and a quarantined community requires an
opted-in logged-in user, which this client is not and cannot become. Whether
NSFW-flagged communities are reachable is the open question in issue #3 — it matters
because true-crime subreddits are frequently NSFW-flagged, and with credentials off
the table there is no fallback if the answer is no. That makes #3 a
scope-determining spike rather than a configuration detail.

**Telegram** — a bot token from `@BotFather`.

**Ollama** — stays a **host service**, not a compose service: it already holds the
GPU and the pulled models, and duplicating it would mean passing the GPU through for
no gain. The container reaches it via `host.docker.internal` with
`extra_hosts: host-gateway`.

## Configuration

One `pydantic-settings` model reading environment variables, validated at startup so
a missing or malformed value kills the process immediately rather than surfacing as
a mystery failure on the first command.

| Variable | Default |
|---|---|
| `TELEGRAM_BOT_TOKEN` | — |
| `TELEGRAM_OWNER_ID` | — |
| `REDDIT_USER_AGENT` | — |
| `REDDIT_MIN_REQUEST_INTERVAL` | `10s` |
| `DATABASE_PATH` | — |
| `OLLAMA_HOST` | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | `qwen3.5:4b` |
| `DIGEST_TIMEZONE` | `America/Sao_Paulo` |
| `DIGEST_SEND_WINDOW` | `08:00–22:00` |
| `DIGEST_INTERVAL_DAYS` | `7` |
| `DIGEST_POSTS_PER_SUB` | `5` |
| `DIGEST_FETCH_DEPTH` | `25` |
| `DISCUSSION_TOP_COMMENTS` | `8` |
| `DISCUSSION_CHAR_BUDGET` | `6000` |
| `BRIEF_CHAR_TARGET` | `1500` |

There is no `DISCUSSION_REPLY_DEPTH`: the feeds carry no threading, so there is
nothing for it to control.

Secrets live in a gitignored `.env` mounted into the container — the Telegram token
is now the only true secret, since Reddit needs no credentials. Slice 1 needs the
Telegram, Reddit and database rows.

## Failure behavior

1. A handler never lets an exception reach the Owner as a stack trace. It logs in
   English and replies in pt-BR.
2. **The bot is never silent toward the Owner.** Every command gets a reply, and a
   Digest that finds nothing new still says so. Silence is indistinguishable from a
   dead bot, which is this design's principal failure mode.
3. **A non-owner gets no response at all.** This is not an exception to rule 2 —
   rule 2 governs replies to the Owner. Silence toward strangers keeps the bot from
   advertising itself to anyone who finds it.
4. **Per-Subscription isolation during a Digest.** Each Subscription's fetch
   succeeds or fails independently, with up to 3 retries and exponential backoff
   inside the run to absorb Reddit's instability. Whatever still fails is named in
   the Index and skipped for that Digest. There are no follow-up or addendum
   messages: one Digest produces exactly one Index.
5. **A post deleted or removed on Reddit since its Digest** gets its own pt-BR
   message when tapped.

## Telegram interaction

**Index** — the message body carries one numbered line per post: number, subreddit,
pt-BR title, its rank for the week, and a marker for bodyless posts. No score, no
comment count — those do not exist (see Reddit access).

**The Index has to fit one message, and the intended set strains that.** Nine
Subscriptions at `DIGEST_POSTS_PER_SUB` = 5 is 45 numbered lines and 45 buttons,
against Telegram's 4,096-character cap. A translated title alone can run 80
characters, so the default configuration overflows. Slice 2 resolves it by lowering
`DIGEST_POSTS_PER_SUB` — 3 gives 27 entries, which fits — rather than by splitting
the Index across messages: one Digest produces exactly one Index, and that rule is
load-bearing for the "never silent, never spammy" behavior. The value is
configuration precisely so this is a dial and not a rewrite. Below it, a
compact keyboard of numbered buttons. `callback_data` carries only a `digest_posts`
row ID, comfortably inside Telegram's 64-byte cap.

**Tap** — answer the callback immediately, post a "gerando o briefing…" placeholder,
then **edit that message** with the Brief. A cold model load takes seconds and an
unanswered callback spins forever. Ollama's `keep_alive` holds the model resident
between taps.

**Brief length** — Telegram caps messages at 4096 characters. A Brief is budgeted to
fit one message: `BRIEF_CHAR_TARGET` in the prompt, hard-capped, truncated at a
sentence boundary with the permalink appended. A Brief needing 4,000 characters is
not a brief — the limit is a feature, and it keeps the single-message edit intact.

## Slices

### Slice 1 — Subscriptions only

No fetching, no model, no scheduler. Owner-locked, all replies in pt-BR.

| Command | Behavior |
|---|---|
| `/start` | Greet and explain, in pt-BR |
| `/add <subreddit>` | Normalize, validate against Reddit, persist |
| `/list` | Show current Subscriptions |
| `/remove <subreddit>` | Hard-delete one |

**Normalization** — `python`, `r/python`, `/r/python`, and a pasted
`reddit.com/r/python/` URL all resolve to the same Subscription. Anything that is
not a legal subreddit name (3–21 characters, alphanumeric plus underscore) is
rejected before spending a network call.

**Validation** — `/add` fetches the subreddit's feed for real. That is the reason to
do this slice first: it proves feed parsing, request pacing, 429 backoff, and error
handling work before anything expensive is built on them.

Failures are distinguished by HTTP status, which is all the feeds give:

| Status | Meaning | Owner sees |
|---|---|---|
| 200 | readable | added |
| 404 | no such subreddit | "does not exist" |
| 403 | private, banned, or quarantined — **indistinguishable**, all return the same `forbidden` body | one "cannot be read" message naming all three possibilities |
| 429 | rate limited | retried with backoff; only a persistent 429 surfaces, as "try again shortly" |
| other / network | unreachable | "Reddit unreachable" |

Collapsing 403 is a deliberate loss, not an oversight: telling the Owner "private"
when the subreddit is actually quarantined would be a confident wrong answer, and
the feed carries nothing that separates them. Already-subscribed, and `/remove` on a
Subscription that does not exist, each get their own message rather than silently
succeeding.

NSFW needs no branch here — see Subscriptions worth having, which settles what is
readable and why `r/MorbidReality` is not.

**Testing** — unit tests for normalization and `store`; handler tests against a fake
Reddit client and fake Telegram context, where every status branch above is
exercised; one marked contract test against real Reddit, paced slowly, so the
default suite stays offline and deterministic.

### Slice 2 — Briefs, triggered manually

`/brief` **forces a Digest and stamps `last_digest_at`**, exactly as the scheduled
tick would — one code path, no preview-versus-real distinction. Delivers the Index,
produces Briefs on tap, and ships the eval harness. Fully useful without automation.

`/brief` always replies, even when nothing is new.

### Slice 3 — Catch-up-on-wake scheduler

Startup and hourly tick, elapsed-interval check, send window.

Each slice gets its own spec before implementation.

## Future work

**Custom ranking is abandoned, not deferred.** An earlier revision planned two
refinements over Reddit's `top?t=week` — *engagement weighting* (blending score with
comment count, since Briefs summarize Discussion and comment volume is the better
proxy for brief-worthiness) and *baseline-relative scoring* (normalizing against a
subreddit's typical top-post score, so a small community's breakout post can outrank
a large one's routine post). Both need score and comment count. Neither is reachable
from the Atom feeds, and the API access that would have supplied them was refused
([ADR-0005](../../adr/0005-rss-is-the-permanent-source.md)).

They are recorded here because the ideas remain sound and would become available
immediately if Reddit's access policy ever reopens. Until then, Traction is Reddit's
ordering and there is nothing to tune.

**Discussion selection quality**, by contrast, *is* tunable and is where ranking
effort now goes. "First N feed entries, flat" is the weakest link in the design; the
eval harness exists to find out how weak.

## Out of scope

- **Multi-user support, per-user quotas, cost accounting** — there is one Owner, and
  each would shape the schema around a need that does not exist.
- **Fetching linked articles** — adds scraping, paywalls, and failure modes.
- **Browsing past Digests.**
- **Any web UI.**
