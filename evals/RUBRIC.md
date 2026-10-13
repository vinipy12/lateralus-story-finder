# How the two arms get compared

ADR-0003 set a quality gate: real threads run through both the local model and
Opus 5, compared side by side, before committing to local inference. This is how
that comparison is scored, written down before the outputs exist so the bar is not
adjusted to fit whatever comes back.

## Gate 0 — shippability, pass/fail

Two checks, both mechanical, both disqualifying:

**0a — structural validity.** Does the model emit a parseable `Brief` with
`title_pt` and `discussion_pt` as strings?

The spec has `summarizer` returning a **validated** `Brief` so malformed output
fails loudly at the boundary. A model that cannot reliably produce the shape is
disqualified no matter how good its prose is, because in production that output
never reaches the chat — it raises.

**0b — cap compliance.** Is `discussion_pt` ≤ 2400 and `content_pt` ≤ 1200?

Added after run-004, where the local model produced four over-cap Briefs that
*parsed*. A Brief that exceeds the budget is a contract failure even when it is
valid JSON: the caps exist so one Brief fits one Telegram message, and an
over-cap Brief cannot ship as written. Code must still hard-cap and truncate at
a sentence boundary — every run so far has shown prompt-only length control is
unreliable in both directions — but a model that routinely overruns is telling
you it cannot budget, and truncation will be cutting its content for it.

**A single failure in 12 is not noise.** It is one Digest entry a week that dies
when the Owner taps it.

## The five dimensions, scored 1-5 per fixture

Score both arms on the same fixture back to back, not one arm all the way through.
Comparative judgement is far more reliable than remembered absolute judgement.

| # | Dimension | 5 | 1 |
|---|---|---|---|
| 1 | **Naturalness** | Reads as written by a Brazilian | Word-order calques, English idiom translated literally |
| 2 | **Tone fidelity** | Sarcasm reads sarcastic, dread reads dreadful | Flattened into neutral description; jokes explained rather than landed |
| 3 | **Factual fidelity** | Names, dates, places, numbers intact; proper nouns untranslated | Invented details, mangled dates, translated place names |
| 4 | **Stance attribution** | Who holds which position is right, including "nobody agrees" and "this one is neutral" | A stance assigned to someone the source does not support; an accusation softened into a suggestion |
| 5 | **Discussion coverage** | The thread's actual substance and its disagreements | Summarizes the post body and ignores the comments |
| 6 | **Usefulness alone** | Stands by itself; no need to open Reddit | Requires the original to make sense |

**Dimension 4 was added after run-004** and is the one to watch now. The judge's
deciding call turned on it: an arm that had correctly said the author stood alone
then promoted a stance-free one-line exclamation into a believer. That is not a
tone problem and not quite a factual one, and it was getting scored under both.

It deserves its own line because the input makes it hard by construction. RSS
carries no authors and no threading, so the model reconstructs "who said what"
from flat text alone. Preserving a hedge counts here too: turning a commenter's "I'm not sure
this is true" into a fact is a stance error, and on true-crime
material removing a hedge from an allegation is as damaging as inventing a date.

Two related errors score here rather than elsewhere:

- **Provenance drift** — moving a commenter's assertion into `content_pt`, so the
  listener can no longer tell whether it came from the post or the thread.
- **Manufactured neutrality** — reporting a hostile thread as balanced.

Dimension 2 remains the subtlest to spot. It is where small models are weakest,
it is nearly invisible in a quick skim, and on this content it is the difference
between a brief worth reading and a flat recap.

## What decides it

**Not the mean.** Averaging hides the failure that matters: a model that scores 4s
across eleven fixtures and invents a detail on the twelfth is worse for true-crime
material than one that scores a consistent 3.

Decide on:

1. **Gate 0 pass rate**, both halves — anything below 12/12 on validity *or* cap compliance needs explaining before anything else is discussed.
2. **Any factual invention at all** (dimension 3 scoring 1-2). On this subject matter that is close to disqualifying on its own.
3. **Any unsupported stance** (dimension 4 scoring 1-2). One invented believer is a failed reconstruction, not a rounding error.
4. **The floor, not the ceiling** — the worst fixture of the twelve, per dimension.
5. **Tone fidelity gap** between the arms, which is the specific thing a small model is expected to lose.
6. **Latency**, last *for a hosted model*. `keep_alive` holds a local model resident between taps, so a slow first load matters much less than a bad brief.

   The exception is a local model on hardware that cannot hold it. Briefs are
   produced lazily, on tap, so a 113-second generation is the Owner sitting and
   waiting on every single tap while the machine is occupied. That is a product
   property, not a benchmark number, and it should count against an otherwise
   equal local arm.

## Honest limits of this eval

- **12 fixtures is a small sample**, chosen for failure-mode coverage rather than representativeness. It can show that a model *fails*; it cannot establish a reliable pass rate.
- **The judge is not blind.** Whoever scores knows which arm is which, and Opus is the reference. Expect that to flatter Opus, and weight clear defects in the local output over close calls.
- **Judging pt-BR quality is the Owner's call, not the agent's.** An agent can flag invention and structural failure; whether a translation *sounds Brazilian* is a native-speaker judgement.
- **A single run per fixture establishes a failure, never a pass rate.** A hard failure is evidence against an arm. A clean 12/12 is *not* a reliability estimate — it is one sample. Before a route is made permanent, re-run the winner on the highest-risk fixtures across independent trials, and keep the trials genuinely independent: one agent generating three samples anchors on its own first answer and measures self-consistency instead of variance.
- **Self-report integrity is an eval-operations problem, not a model-quality one.** An arm was discarded in run-004 for fabricating shortened inputs and then reporting a clean run. None of that belongs in a model's score — but it is why prompts are materialised to disk under `runs/run-004/prompts/`, why every arm is checked against a `prompt_chars` manifest, and why a clean self-report is never accepted as evidence. Trust artifacts, not an arm's claim about itself.
- **Rule 10 is untested.** No fixture is in Portuguese — the manifest says so explicitly, after scanning 415 posts. Any shipped prompt carries one rule this eval has never exercised.
- **"Conte TUDO" is not literally compatible with a hard budget.** Judge whether all material *positions* and salient unique details survived, not whether every clause did. Counting an omitted low-value detail the same as a dropped disagreement rewards length over judgement.

## If the local model fails the gate

That is a finding, not a setback — it is exactly what ADR-0003 built the seam for.
Record it, keep the fixtures, and swap the implementation behind `summarizer`. The
fixtures stay valid across any model, which is the reason they exist.
