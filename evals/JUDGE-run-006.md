# Codex arms — run-006, judged 2026-08-22

Three Codex CLI models on the same 12 fixtures and the identical shared prompt.
Judged by me against `evals/RUBRIC.md`, including the dimension 4 (stance
attribution) and two-part Gate 0 added after run-004.

| arm | model | Gate 0a structural | Gate 0b caps | mean | disc min/med/max |
|---|---|---|---|---|---|
| `sol` | `gpt-5.6-sol` | **12/12** | 5/12 clean | 34.9s | 1210 / 2311 / 2800 |
| `terra` | `gpt-5.6-terra` | **12/12** | **7/12 clean** | **25.2s** | 1114 / 1899 / 2776 |
| `gpt55` | `gpt-5.5` | **12/12** | 2/12 clean | 28.5s | 1489 / 2669 / 3887 |

## Read the cap column with care — the comparison is not like-for-like

**The Codex arms are one-shot; the Claude arms were not.**

`run_codex.py` calls the model directly and parses whatever comes back, exactly
as the Ollama arm does. The Claude arms went through an agent harness that read
files and wrote JSON itself, and could revise before anything reached disk.
Their own reports say they did: Sonnet needed *"2-6 rounds of trimming to land
under budget"*, and Opus reported four fixtures each needing 600-1,150 characters
cut from a first draft.

So Sonnet's 0/12 over cap is a **post-revision** number and sol's 5/12 is a
**first-draft** number. They are not the same measurement.

What that leaves is a finding rather than a ranking: **every model tested,
Claude included, overruns the cap on first draft.** Three runs and seven models
have now failed to control length by instruction. The cap belongs in code with
sentence-boundary truncation, as the spec already requires. Judging an arm on
first-draft length here would be judging it on the wrong thing.

## Gate 0a: all three are perfect, and that is the real result

**Zero malformed JSON across 36 generations**, and 36 more in the discarded first
pass — 72 total. No missing fields, no unescaped control characters, no duplicate
keys.

For contrast, on the identical fixtures the local `qwen3.5:4b` failed
`F02-hostile-thread` twice with an unescaped control character, and it is the
same fixture that is hardest here. On the half of Gate 0 that actually raises in
production, Codex matches Claude and beats local decisively.

## The deciding fixture: `F02-hostile-thread`

The hostile thread. Nobody but the author believes the story; the closing
exclamation takes no side; a link-drop followed by a sarcastic "sure, I bet it's
true" is sarcasm, not support.

All three caught the AI accusation, the timeline inconsistency, and the explicit
charge that the story is a lie, including the taxi-scene tell. Where they part:

**`sol` — correct.** Marks the sarcasm explicitly, and reports the closing
comment as a bare reaction without assigning a stance.

**`gpt55` — minor stance error.** Marks the sarcasm correctly, but renders the
closing comment as someone shocked by the story — attaching the
shock to the story specifically, where the source cannot distinguish shock at the
story from shock at the fight in the comments. Milder than Opus's invented
believer, same category.

**`terra` — real stance error.** It reports the sarcastic link-drop flat, as someone
posting a link and saying they bet it is true. A listener hears
someone saying they bet it's true, which converts a mocking doubter into a
supporter. That inverts the one thing this fixture tests. It is the same class
of failure that cost Opus the run-004 ranking, and it happened on the arm with
the best cap discipline.

`terra` also **transcribes a raw URL** into the brief. The prompt's premise is
that the Brief gets read aloud; a raw
`reddit.com/r/.../comments/...` string read out loud is unusable. `sol` and `gpt55` both described the link
instead.

## Invention check

Spot-checked `F07-link-post`, the fixture where Haiku fabricated an
entire UAP/military claim in run-004. **No invention from any Codex arm.** All
three correctly reported the moderator-removal notice as an event in the thread
rather than skipping it or inventing around it — the prompt never says how to
handle one, so this is three-for-three on an underspecified case.

## Ranking

1. **`sol` (gpt-5.6-sol)** — the only Codex arm with no stance error on the
   deciding fixture. Full accusation coverage, sarcasm marked, links described
   rather than transcribed. Genuinely competitive prose.
2. **`gpt55` (gpt-5.5)** — same coverage and correct sarcasm, one minor
   unsupported stance, and the loosest length control by a wide margin (median
   2669, max 3887).
3. **`terra` (gpt-5.6-terra)** — fastest and tightest on length, and the only arm
   that inverted a doubter into a supporter. Speed and brevity do not offset a
   stance inversion on true-crime material.

## Against Sonnet

Sonnet still leads, on the one dimension where the comparison is clean.

Across three independent variance trials Sonnet refused to assign a stance to
the closing comment **3/3**, each time explicitly saying the source does not
show which side it points to. `sol` got it right once. That is one sample against
three, and by this eval's own rule a single clean generation establishes nothing
about reliability.

**Recommendation unchanged: ship Sonnet.** `sol` is a credible alternative and
the best non-Claude arm tested — if it were run through an equivalent
revise-loop harness and held 3/3 on a variance check, it would be a real
contender. On present evidence it has one clean sample where Sonnet has three.

## What this run adds

- **Codex models are structurally excellent.** 72/72 valid JSON. If the Brief
  schema were the only concern, any of the three would ship.
- **Cap compliance without a revision loop is a property no model has.** That
  question is closed; it is a code problem.
- **Stance attribution keeps deciding this eval.** It has now separated the
  arms in run-004 (Opus) and run-006 (terra, gpt55), across two vendors. Adding
  it as its own rubric dimension was correct.
