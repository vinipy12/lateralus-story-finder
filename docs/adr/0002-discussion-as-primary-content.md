# Discussion is a Brief's primary content, not the post body

The obvious model is that a Brief summarizes a post's body, with comments as
supporting colour. That model breaks on Reddit: a large share of top-of-week posts
are link or image posts with no body at all, and this project deliberately does not
fetch linked articles. Under the obvious model those posts would produce empty
Briefs.

So the relationship is inverted. Discussion — the post's comment threads — is the
primary content of every Brief, and the body is optional enrichment that is simply
absent on link and image posts. This is also truer to how Reddit is actually read:
on an image post, the thread *is* the substance.

## Consequences

`Brief.content_pt` is nullable while `discussion_pt` is always present — the reverse
of what a reader would expect, and the reason this is written down. It also makes
Discussion selection load-bearing rather than a detail: how many threads, how deep,
and within what character budget directly determines Brief quality, which is why
those are tunable configuration backed by an eval harness rather than constants.

## Amendment, 2026-08-20

Discussion is reachable over RSS, so this decision stands. Its *shape* does not:
the RSS comment feed is flat and unscored, carrying no score, parent, depth, or
in-reply-to fields. "Top threads by score, with replies" was written against an API
this project does not currently have.

Selection therefore takes the first N feed entries. The feed follows Reddit's own
comment ordering rather than recency, so this approximates the intent without
implementing it. See [ADR-0004](0004-rss-as-a-degraded-fallback-adapter.md).

## Amendment, 2026-08-21

The Reddit API access request was refused, so the flat unscored shape above is
permanent rather than provisional and "the RSS adapter" is simply how this project
reads Reddit. See [ADR-0005](0005-rss-is-the-permanent-source.md).
