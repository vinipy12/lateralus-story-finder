# RSS is the permanent Reddit source

Supersedes the temporary framing in
[ADR-0004](./0004-rss-as-a-degraded-fallback-adapter.md).

The Reddit API access request submitted 2026-08-20 was **refused on 2026-08-21**.
The stated reason was boilerplate — the submission "is not in compliance with
Reddit's Responsible Builder Policy and/or lacks necessary details" — with no
specific defect named and no appeal path offered. Self-service app creation remains
closed, so there is no other route to credentials.

ADR-0004 pre-committed to what happens here: on refusal, RSS stops being temporary
and the design is rewritten around it rather than left carrying an aspirational API
path nobody can act on. That is what this ADR does. **Public Atom feeds are the
source. There is no API adapter.**

The timing is as good as it could have been. Nothing in `src/` or `tests/` had been
built against the API yet — the `reddit` module did not exist. The API assumptions
lived only in documents, so committing to RSS cost four file edits rather than a
migration.

## Considered options

**Resubmit a corrected request.** The "or lacks necessary details" half of Reddit's
refusal arguably invites a better-detailed second attempt. Rejected as the *primary*
path, not forever: Reddit's policy prohibits duplicate requests for the same use
case, a second refusal carries account risk, and there is no SLA, so the project
would be blocked indefinitely on a coin flip. If a corrected request is ever filed
it is a deliberate decision made on its own terms — approval would then be a
capability *upgrade* against a working system, not the unblocking of a stalled one.

**Undocumented `.json` endpoints.** They return 403 from a residential connection
and are increasingly blocked. Not viable.

## Consequences

**The API-only fields leave the data model.** `RedditPost.score`,
`RedditPost.num_comments`, `Comment.score`, `Comment.depth`, and the
`DISCUSSION_REPLY_DEPTH` setting described data no adapter will ever populate.
ADR-0004 argued for keeping them precisely because approval would have switched them
on with no code change; that argument is now dead, and carrying fields the system
cannot fill is how a schema starts lying.

**`Brief.source` goes too.** It existed to keep Brief quality from being compared
across two pipelines unaware. With one pipeline there is nothing to distinguish, and
no Briefs have been produced under the old scheme.

**The `reddit` module seam stays.** It was never justified by the two-adapter
situation — it is the boundary that keeps feed-parsing details out of `digest` and
`bot`. A future adapter, if one is ever warranted, still drops in behind it.

**Discussion selection is flat and unranked, permanently.** No per-comment score
means "top N comments by score" becomes "first N feed entries", following Reddit's
own comment ordering. This is an approximation of the intent and the eval harness
should be pointed at it early — it is now the *only* selection strategy, not a
degraded stand-in for a better one arriving later.

**Custom ranking is off the table, not deferred.** The Future work section proposed
engagement weighting and baseline-relative scoring, both of which need score and
comment count. Neither is reachable from RSS. Traction is Reddit's `top?t=week`
ordering and that is the end of it.

**Rate limiting is now a first-class design constraint rather than a development
nuisance.** Live probing on 2026-08-21 returned 429 at one request every 9 seconds
from a residential connection, against roughly 100 requests/minute on the API tier
the project will never have. Five requests per week is far inside any budget, but
`/add` validation is Owner-triggered and can burst, so request pacing belongs in the
`reddit` module rather than in the caller's discipline.
