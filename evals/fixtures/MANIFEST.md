# Translation eval fixtures

**The three files in this directory are synthetic.** The posts, comments, usernames,
subreddits and IDs are invented. They exist so the harness runs end to end and so the
input format is visible.

The eval itself was run against twelve real Reddit threads gathered from public RSS
feeds. Those fixtures, and every per-run model output, are kept out of the public
repository: they are other people's posts and comments, some about real cases
involving real people. The judge and results documents in `evals/` refer to them by
neutral labels (`F01-long-narrative` … `F12-anecdotal-thread`) and keep only
aggregate findings; each `runs/run-00N/COMPARISON.md` keeps only its structural
(Gate 0) table.

## Format

One JSON object per thread, consumed by `build_prompt.load_fixtures` in filename
order:

| Field | Meaning |
|---|---|
| `id`, `subreddit`, `rank` | identity and rank within the week's listing |
| `title`, `author`, `permalink`, `url`, `created_utc`, `is_self` | from the listing feed |
| `selftext` | post body; empty for link and image posts |
| `comments` | flat list of `{id, author, body}`, in feed order |
| `fetched_at` | when the fixture was gathered |
| `exercises`, `notes` | which failure mode the fixture covers, and why it is hard |

There is no `score`, `num_comments` or comment `depth`, because the RSS source never
provides them (ADR-0005). Only `subreddit`, `title`, `selftext` and comment `body`
reach the model.

## How the real set was built

Listings came from `https://www.reddit.com/r/<NAME>/top/.rss?t=week&limit=100`,
comments from `https://www.reddit.com/r/<NAME>/comments/<ID>/.rss?sort=top&limit=100`.
Bodies and comments are the Atom `<content>` element, HTML-unescaped and stripped of
tags. `[deleted]`, `[removed]` and AutoModerator entries were dropped, then the first
8 survivors kept (`DISCUSSION_TOP_COMMENTS`). The twelve covered long and very short
self-posts, empty-body link and image posts, sarcasm, profanity, forensic and
statistical jargon, a hostile Discussion that disputes the author, and a moderator
removal notice. No Portuguese-language post was found, so the "already in Portuguese"
path is untested.

## The synthetic set

| File | Shape |
|---|---|
| `ExampleMysteries-synth01.json` | narrative self-post; competing explanations, a hedge, an author reply, sarcasm |
| `ExampleCampfire-synth02.json` | question post with an empty body; the Discussion is the content |
| `ExampleOddities-synth03.json` | image post with no body; includes a moderator-removal notice |
