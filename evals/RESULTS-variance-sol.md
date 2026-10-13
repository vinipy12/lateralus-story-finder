# sol variance check — run-007, 2026-08-22

`JUDGE-run-006.md` closed with the one thing that would change the
recommendation: *"`sol` got it right once. That is one sample against three, and
by this eval's own rule a single clean generation establishes nothing about
reliability."*

Three independent `gpt-5.6-sol` trials on the same three fixtures the Sonnet
variance check used, so the two are directly comparable.

## Independence is architectural here, not lucky

Run-005 filed a harness failure: three Sonnet trials shared one scratchpad, and
one trial's file was silently overwritten by another's. Independence was verified
after the fact via Jaccard rather than guaranteed.

That cannot recur here. Each trial is a separate `codex exec` process with no
shared state, no filesystem access, and no memory of the others — the same direct
call `run_codex.py` made in run-006, on unmodified code. The fixture subset was
supplied as a directory of symlinks so the script itself is byte-identical to the
one that produced run-006.

## Gate 0a — 9/9

Nine of nine parseable, every required field present, `content_pt` null on
exactly the one empty-body fixture (`F07-link-post`) all three times. Codex's
structural record is now 81/81 across run-006 and run-007.

## Gate 0b — 5/9 over cap, and still not the comparable number

| fixture | t1 | t2 | t3 |
|---|---|---|---|
| `F02-hostile-thread` | 1506 / 1184 | 1493 / **1304** | 1731 / **1563** |
| `F09-statistics-jargon` | **2450** / **1357** | 2259 / **1545** | 2389 / **1515** |
| `F07-link-post` | 1391 / null | 1333 / null | 1362 / null |

(`discussion_pt` / `content_pt`, caps 2400 / 1200; over-cap in bold.)

Overruns are `content_pt` in four of five cases, and `sol` never missed the
`discussion_pt` cap by more than 50 characters. As in run-006 this is a
first-draft number against Sonnet's post-revision one, so it does not rank the
arms — it re-confirms the finding that no model controls length by instruction.

## The deciding property: stance on `F02-hostile-thread`

Two things this fixture tests. The sarcastic link-drop ("sure, I bet it's true")
is sarcasm, and the closing exclamation takes no side.

**All three trials got both right.**

| | sarcasm marked | closing comment |
|---|---|---|
| t1 | yes, explicitly as irony | reported as a bare exclamation |
| t2 | yes, explicitly as irony | reported as a bare reaction |
| t3 | yes, explicitly as irony | reported as a bare reaction |

(The trials' exact wording is omitted from the public repository because it
renders a real Reddit thread.)

No trial promoted the closing comment into a believer, and no trial reported the
sarcastic link-drop flat — `terra`'s run-006 failure. All three also kept the
accusation as an accusation (the story called a lie), including the
taxi-scene tell, rather than softening it into a suggestion.

**Links described, never transcribed, 9/9.** `terra` put a raw
`reddit.com/r/...` string into a brief meant to be read aloud; `sol` did not do
this once across nine generations. The only English surviving anywhere is
one proper name, which rule 8 requires.

## Invention and hedges

**No invention on any of the nine.** On `F09-statistics-jargon` all three trials reproduced
the same eight percentages — 53,7 / 3,1 / 6,5 / 4 / 2,9 / 2,6 / 1,9 / 3,6 —
identically and with pt-BR decimal commas. On `F07-link-post` all three handled
the moderator-removal notice as an event in the thread, and all three preserved
the doubter's hedge (an explicit willingness to be proven wrong), which the rubric scores under dimension 4.

## Two blemishes, both minor, both in t1

- **Provenance merge.** On `F07-link-post`, t1 attributes one
  explanation to the same person who linked a news article; the source has
  them as two separate comments. t2 and t3 kept the voices apart. Since the input
  carries no authors and no threading, this is a defensible reconstruction — but
  it does collapse two commenters into one.
- **Filled-in truncation.** The linked post's title is cut off mid-sentence in the
  source; t1 completes it with an invented ending. Rule 8 says leave ambiguity
  ambiguous. t3 does the same thing with a different ending; t2 paraphrases
  without committing to a title.

Neither is a stance error and neither touches the deciding property.

## Verdict

**`sol` now has the same 3/3 record on the deciding property that Sonnet has**
(4/4 counting its run-006 generation). The single-sample objection in
`JUDGE-run-006.md` is answered.

What still separates them is the harness, not the model. Sonnet's numbers come
from an agent loop that could revise before writing; `sol`'s come from one shot.
On the dimensions where the comparison is clean — structural validity, stance
attribution, factual fidelity, hedge preservation — **`sol` is now level with
Sonnet on this fixture set.** On cap compliance it is not, and cannot be compared
until it is run through an equivalent revise loop.

**Recommendation: ship Sonnet for now — `sol` stays in the running.**

`sol` is not disqualified by the evidence in this eval. It matched Sonnet 3/3 on
the property that had been deciding the eval, with no invention and no URL
transcription across nine generations.

**Owner decision, 2026-08-22: paid API usage is acceptable.** That settles the
procurement question this section previously treated as a blocker. The spec's
note at [spec:119](../docs/superpowers/specs/2026-08-20-story-finder-design.md)
— that Codex/ChatGPT *subscription credits* cannot back a programmatic API key —
remains true and remains the reason `codex exec` cannot be the production path.
It is no longer a reason to drop the model. Cost was never the obstacle: run-004
priced the entire decision at $8–20/year and called it too small to matter.

### What is still unmeasured — for both arms, not just `sol`

**Owner, 2026-08-22: the Anthropic subscription cannot power this project
either.** Sonnet would be called through the API, exactly like `sol`. That
collapses the asymmetry this document previously asserted.

Provenance, checked rather than assumed:

- At the time, `evals/` held only `run_ollama.py` and `run_codex.py`. **There was
  no Anthropic runner**, and no `anthropic` dependency in `pyproject.toml`.
  (`run_anthropic.py` and `run_openai.py` have since been added, along with an
  `evals` extra in `pyproject.toml`; no results from them are recorded yet.)
- Every Sonnet/Opus/Haiku record carries `seconds: None, raw: None`. No script
  wrote them; subagents on the Owner's Claude Code subscription produced the JSON
  by hand, with file access and unlimited revisions.

| arm | how measured | production shape? |
|---|---|---|
| Sonnet / Opus / Haiku | agent harness, revise loop | **no** |
| `sol` / `terra` / `gpt55` | one-shot direct call | **yes** |
| `qwen3.5:4b` | one-shot direct call | yes |

**No arm has been measured on its production path except the local one**, and the
bias runs against the arms measured honestly.

This inverts the cap argument every judge doc since run-006 has made. Sonnet's
0/12 is a pure artifact of the loop — its own report says *"2-6 rounds of
trimming to land under budget."* If `summarizer` is one-shot, the first-draft
number is the relevant one and the post-revision number is the irrelevant one.
**One-shot Sonnet has never been measured.** The 3/3 stance result is
contaminated the same way: a revise loop can catch a stance error before it
reaches disk.

Availability is also unverified for both: whether `gpt-5.6-sol` is served on the
OpenAI API, and under what id, has not been checked from inside this repo.

## What would settle it

The eval needs one thing it has never had: **an API runner for every arm, and a
round where all of them are called the same way.**

1. **Write `run_anthropic.py`** mirroring `run_codex.py` — direct call, strict
   parse, no revision. This is the missing half of the harness, not a new
   feature.
2. **Confirm `gpt-5.6-sol` is served on the OpenAI API** and under what id.
   Everything about `sol` is void if it is CLI-only.
3. **Re-run the three variance fixtures one-shot on both APIs**, three trials
   each. This is the first honest head-to-head the project will have had.
4. **Then all 12 fixtures**, and rank on those numbers.

Expect the ranking to move. Sonnet loses a revise loop it has always had here;
`sol` loses nothing, because it never had one. Whether Sonnet's stance
reliability survives one-shot is genuinely unknown, and it is the single most
important open question in this eval — more than anything about `sol`.

Runs 001-007 do not become worthless. They established the fixtures, the rubric,
the prompt, and that stance attribution is the dimension that separates models.
What they cannot do is decide what to ship.