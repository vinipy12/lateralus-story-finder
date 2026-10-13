# Story Finder

A single-user Telegram bot that tracks subreddits, gathers each one's
highest-traction posts weekly, and briefs them in Brazilian Portuguese.

## Language

**Subscription**:
A subreddit the owner tracks. Identified by its normalized subreddit name.
_Avoid_: feed, source, channel

**Digest**:
The weekly run that gathers posts for every Subscription. The run itself — never
the message it produces. A post appears in at most one Digest, ever: a post carried
by an earlier Digest is never carried again, whatever its current Traction.
_Avoid_: batch, job, roundup

**Index**:
The message listing the posts a Digest gathered, with translated titles and each
post's standing for the week. One Index per Digest.
_Avoid_: digest message, summary list, table of contents

**Brief**:
The Brazilian Portuguese rendering of one post — its discussion, and its body when
it has one. Produced on demand when the owner opens a post from an Index, then
cached.
_Avoid_: summary, translation, digest entry

**Traction**:
A post's standing within its subreddit for the week, as ranked by Reddit's own
top-of-week ordering. A rank, never a number — no score or comment count is
available to this project.
_Avoid_: popularity, score, engagement

**Discussion**:
The comment threads on a post. The primary content of a Brief — for link and image
posts it is the only content.
_Avoid_: comments section, replies

**Owner**:
The single Telegram user the bot answers to. Every other user is ignored.
_Avoid_: user, admin, subscriber
