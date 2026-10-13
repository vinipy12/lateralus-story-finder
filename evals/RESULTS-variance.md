# Sonnet variance check — run-005, 2026-08-21

The judge's caveat on run-004: *"One generation per fixture establishes a
failure, not reliability."* Sonnet's clean 12/12 was one sample, not a pass rate.

Three **independent** Sonnet trials on the three highest-risk fixtures. Separate
agents, blind to each other, blind to run-004's output and to the judge's
verdict — all three contain the answer to the question being tested.

Deliberately not one agent producing three samples: it would anchor on its own
first answer and measure self-consistency rather than variance.

## Gate 0 — 9/9 on both halves

| fixture | t1 | t2 | t3 |
|---|---|---|---|
| `F02-hostile-thread` | 2345 / 1200 | 2094 / 1200 | 1744 / 1196 |
| `F09-statistics-jargon` | 2362 / 1176 | 2365 / 1030 | 2292 / 1145 |
| `F07-link-post` | 1543 / null | 1429 / null | 1335 / null |

(`discussion_pt` / `content_pt`, caps 2400 / 1200.)

Nine of nine parseable, nine of nine inside both caps, nine of nine verified
against the `prompt_chars` manifest. `content_pt` null on exactly the one
empty-body fixture, all three times.

## The deciding property: stance on `F02-hostile-thread`

This is where Opus failed run-004 — it correctly said the author stood alone,
then promoted the stance-free closing exclamation into a believer.

**All three trials got it right, and all three refused the same trap:**

- **t1** — says the closing reaction does not make clear whether it is shock at
  the story or at the fight in the comments, and states plainly that only the
  author defends the story as true.
- **t2** — says it cannot be known which side the closing reaction points to.
- **t3** — calls it a shocked reaction that does not take a side on whether the
  story is true.

Three independent generations, three explicit refusals to assign a stance the
source does not support. Each also reconstructed the same structure unprompted:
the author alone asserting truth, three distinct commenters doubting, no third
party siding with her.

None softened the AI accusation into a suggestion. t1 additionally noted it had
kept the accusers as separate unnamed commenters rather than assuming one
person, *"since the source gives no way to tell"* — correct, and the input
genuinely carries no authors.

## Verdict

**Sonnet's run-004 result holds under repetition on the fixtures most likely to
break it.** Ship it, subject to the Owner's native pt-BR read-aloud check, which
remains the one dimension this eval does not decide.

## Independence caveat — recorded rather than glossed

The three trials shared one session scratchpad. Trial 3 reported that a file it
wrote there was silently overwritten in place by another trial's, and that the
content was a sibling trial's brief for two of the same fixtures.

Independence was verified after the fact rather than guaranteed by design:

- Trial 3 had drafted its briefs before touching the scratchpad and said so
  unprompted, then moved to a private subdirectory.
- Pairwise Jaccard on the nine `discussion_pt` outputs is **0.36–0.50**,
  consistent with independent summaries of shared source material. Copying would
  sit near 0.9.

The measurement stands, but the isolation was luck, not architecture. Future
parallel trials get one working directory each. Filed as a harness failure.
