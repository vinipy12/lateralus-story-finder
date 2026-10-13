# RSS is a temporary degraded adapter, not the intended design

> **Status: superseded by [ADR-0005](./0005-rss-is-the-permanent-source.md)
> (2026-08-21).** The access request this ADR waited on was refused. RSS is the
> permanent source and there is no API adapter. Kept for its reasoning about what
> the `reddit` seam did and did not change, which still holds — but its instruction
> to preserve the API-only fields is reversed by ADR-0005.

Reddit closed self-service Data API access on 2025-11-14 under its Responsible
Builder Policy; `/prefs/apps` still renders and validates but the create action is
disabled server-side, so no credentials can be obtained without approval. A request
was submitted 2026-08-20 with no published SLA. Meanwhile `.json` endpoints return
403 from a residential connection while public Atom feeds return 200, so the project
reads RSS in the interim.

The important part is what this did **not** change. `reddit` was already the only
module permitted to touch Reddit, so RSS is a second implementation behind that
interface rather than a new design. The spec continues to describe the API path,
because the API path is still the destination; the RSS adapter declares which
capabilities it cannot supply and what each absence degrades to.

## Consequences

**Do not "fix" the spec to match RSS.** A future reader will notice that
`RedditPost` carries `score` and `num_comments` that the running system never
populates, and that `DISCUSSION_REPLY_DEPTH` is configured but ignored. Both are
correct. They describe the API adapter, which becomes active the moment credentials
appear in `.env` — no code change, no migration. Deleting them would mean rebuilding
them on approval.

**Briefs built on RSS are genuinely worse**, and knowingly so. Without per-comment
scores, Discussion selection takes the first N feed entries rather than the highest
rated. The feed follows Reddit's own comment ordering rather than recency, so this
approximates the intent — but it is an approximation. `Brief.source` records which
adapter produced each Brief precisely so that quality is never compared across the
two pipelines unaware.

**If approval is refused**, this stops being temporary and the decision should be
revisited deliberately — rewriting the spec around RSS as the permanent source,
rather than leaving an aspirational API path in a document nobody can act on.
