# Translation eval — results

Twelve fixtures, identical prompt within a run, both arms. Scored against
`RUBRIC.md`.

- **ollama** — `qwen3.5:4b`, local, `think: false`, `num_ctx` 8192, temp 0.2
- **opus** — `claude-opus-5`, the reference

A prompt change invalidates cross-run comparison, so each run is archived whole
under `runs/run-00N/` and both arms are always re-run together. (The public
repository keeps only each run's structural summary; see `fixtures/MANIFEST.md`.)

---

# run-003 (2026-08-21) — current

Prompt rewritten for **spoken** Brazilian Portuguese, on Owner feedback that both
arms were "bloated and too correct" and that a Brief should be readable aloud to
other people. Added a word swap table, a banned-formal-phrase list, and a
read-aloud test. See PROMPT.md's revision history.

## Gate 0 — the local arm fails

| | ollama | opus |
|---|---|---|
| valid briefs | **10 / 12** | 12 / 12 |
| mean seconds | **78.7** (was 45.7) | — |

Two structural failures, both new, both distinct:

- `F02-hostile-thread` — **unescaped control character** in a JSON string. Took
  **280 seconds**, and the model tried to reproduce the 10k-char body nearly
  verbatim into `content_pt`.
- `F09-statistics-jargon` — **duplicate keys**: emitted `content_pt` twice, the
  second time as `null`, and `discussion_pt: null`. The object parses but the
  Brief is empty.

The spec validates `Brief` at the boundary, so both of these raise in production
rather than reaching the Owner. **Two dead taps in twelve.** Run-001 and run-002
were 12/12; the longer, more demanding prompt broke structural reliability.

## The register change worked — spectacularly on Opus

Counting spoken markers (`tá`, `tava`, `pra`, `pro`, `aí`, `só que`, `daí`,
`disse`, `falou`, `contou`) against formal ones (`está`, `afirmou`,
`posteriormente`, `entretanto`, `ademais`…):

| | formal | spoken |
|---|---|---|
| run-002 opus | 4 | 28 |
| **run-003 opus** | **0** | **256** |
| run-002 ollama | 7 | 3 |
| **run-003 ollama** | 17 | 77 |

Opus went to zero formal markers and a 9× increase in spoken ones. Banned phrases
and fabricated consensus are at zero for both arms — the run-002 fixes held.

The local model moved too, but **mixes registers**: its formal-marker count rose
in absolute terms across *fewer* briefs. It is writing spoken and written
Portuguese in the same paragraph.

Comparing the two arms on the same fixture and prompt (sample omitted from the
public repository because it renders a real Reddit thread): the local output carried
a corrupted word, left English slang untranslated (rule 9), and calqued "it's very
much the energy of" word for word. Opus read as speech.

## Length control collapsed on the local arm

| | ollama | opus |
|---|---|---|
| shortest | **326** | 1,306 |
| longest | **5,052** | 1,500 |
| over the 1,500 cap | **6 of 10** | 0 of 12 |

Opus sits in a 1,306–1,500 band on every fixture. The local arm ranges from 326
characters to **5,052** — 3.4× the cap — on the same inputs. Run-002 already
showed it missing in both directions; the spoken register plus "Conte TUDO" made
it far worse.

`F10-case-writeup` got 326 characters against Opus's 1,500 from
identical material. `F11-joking-register` got 5,052.

## Rule 6 versus the cap is now a known, binding conflict

The reference arm reported that **every** eight-comment fixture overran on first
draft by 200–650 characters and needed compression passes, and that eleven of its
twelve finals sit pinned at 1,412–1,500. Spoken register *costs* characters — "só
que" is longer than "entretanto" — while rule 6 forbids dropping detail.

So at eight comments the cap is **binding, not aspirational**, and detail loss is
forced rather than chosen. On `F11-joking-register` the reference arm had to
cut 14 listed anomalies down to about 8. That is real information loss on both
arms, and no prompt wording fixes it — it is a budget problem.

## Verdict

**The local model is out on this evidence**, and the reason changed. Runs 001-002
failed on invented consensus, which a prompt fix solved. Run-003 fails on
capability: it cannot hold JSON, register, and length simultaneously once the
prompt gets demanding. 78.7s mean, two dead taps, and outputs from 326 to 5,052
characters is not a shippable summarizer.

This is exactly the outcome ADR-0003 built the seam for.

Recommended next steps, in order:

1. **Enforce the cap in code.** Three runs, three failures to control length by
   prompt. The spec already requires it.
2. **Judge Opus's run-003 prose for accent** — that is the Owner's call and the
   one thing this eval cannot decide. If the register is right, the prompt is
   settled and the remaining question is only which model runs it.
3. **Try a smaller, non-thinking, non-vision model** before abandoning local
   inference. `qwen3.5:4b` does not fit the 4GB card (6.7-6.9GB, ~50% on CPU),
   and its thinking and vision capabilities are both dead weight here. The
   fixtures are model-agnostic and re-running costs minutes.
4. **If nothing local holds Gate 0 at 12/12, run the summarizer on Opus** and
   revisit the cost assumption in the spec, which currently assumes zero marginal
   cost from local inference.

---

# run-002 (2026-08-21) — superseded

Prompt revised: the anti-consensus rule promoted from 5th to 1st and made
concrete, plus a new rule 2 requiring named attribution. See PROMPT.md's revision
history.

## Gate 0 — structural validity

**Both arms 12/12.** No JSON failures. `content_pt` null on exactly the three
empty-body fixtures in both arms, again.

Local arm: 549s total, **45.7s mean** (up from 37.8s in run-001 — the longer
prompt and longer outputs cost time).

## The rule change worked

**Fabricated consensus phrases: 3 → 0.** Every banned string is gone.

`F02-hostile-thread` — the fixture that failed run-001 by inverting a hostile
thread — now reads correctly as a dispute: the author insists the story is true, other
commenters question whether it was invented, and the author pushes back.

It also recovered a detail from comment 6 that it had missed entirely, and an
English adverb it had left untranslated is now translated.

**What this establishes about the model:** the banned-string approach worked
where it was concrete. Naming the exact phrases to avoid is a pattern match. The
run-001 phrasing — "não invente consenso" — required the model to judge that a
sentence it was about to write *constituted* invented consensus, and it could
not do that. Rules for a 4B model should be matchable, not self-assessed.

## What did not get fixed

**1. The collective voice survives, in a form the banned list does not catch.**
Two of twelve briefs still close with "the community reacts with shock" —
`F02-hostile-thread` and `F04-short-question-profane`. That is the same
speak-for-everyone closing habit rule 1 targets, using words the rule did not
enumerate. On `F02-hostile-thread` it is sourced from a single one-line exclamation.

**2. That same sentence carries a factual inversion.** It says an act of
infidelity happened; the source says an attempt to provoke it **failed**. A reader
takes from the Brief that it happened. Verified against the post body.

**3. Rule 6 was ignored.** `UAP` went from one invented Portuguese expansion to
another — closer, still wrong (*Fenômenos*, not *Objetos*), and rule 6 explicitly says to keep an acronym when
unsure. It expanded anyway. Another judgement-shaped rule that did not land.

**4. The cap regressed.** Overruns went **3 of 12 → 4 of 12**, and the worst case
went from 1,793 to **2,309 characters** — 54% over budget. Rules 1 and 2 ask for
named attribution, which is verbose, so tightening correctness loosened length.
That is a real trade, not a fluke.

## The persistent gap: the local model under-fills

| | ollama | opus |
|---|---|---|
| shortest `discussion_pt` | **646** | 1,195 |
| longest | **2,309** | 1,499 |
| under 1,000 chars | **5 of 12** | 0 of 12 |
| over the 1,500 cap | **4 of 12** | 0 of 12 |

The reference arm lands inside a narrow band every time. The local arm misses in
both directions, and five briefs use under two-thirds of the budget — thin
output regardless of prose quality (dimensions 4 and 5). `F08-forensic-jargon`
got 646 characters against Opus's 1,216 from the same eight comments.

## Verdict

**Improved, still not passing.** Run-001 failed on invented consensus; that
specific failure is fixed. What remains:

- a factual inversion on the highest-signal fixture (dimension 3, which the
  rubric weighs closest to disqualifying),
- the collective-voice habit in 2 of 12,
- systematic under-filling in 5 of 12,
- a cap overrun in 4 of 12 that the prompt cannot fix.

Next, in order:

1. **Enforce the cap in code.** The spec already requires a hard cap truncated at
   a sentence boundary. The prompt has now failed to control length twice, in
   both directions. Stop asking it to.
2. **Extend the banned list** to *"a comunidade"* + reaction verbs, and forbid
   closing sentences that describe a collective reaction. Cheap, and the evidence
   says enumerated patterns are what this model can follow.
3. **Do not add more judgement-shaped rules.** Rule 6's "keep the acronym if
   unsure" was ignored, as was the general anti-invention rule. Two data points
   now say this model follows patterns, not self-assessments.
4. **Re-run both arms and check the inversion specifically.** If a factual
   inversion survives on `F02-hostile-thread`, the local model is out for this
   content — on true-crime material a brief that reverses what happened is worse
   than no brief.

---

# run-001 (2026-08-21) — superseded

Original prompt, with the anti-consensus rule 5th of 7 and phrased as a
principle.

**Gate 0: both arms 12/12.** Local arm 453s total, 37.8s mean.

**Failed on invention.** `F02-hostile-thread` is a hostile thread whose eight
comments accuse the author of writing with AI, name an inconsistency, call the
story a lie, mock it sarcastically and end on a stance-free exclamation. Nobody but
the author believes it. The local arm closed by saying that most people agree the
experience was terrible and the case is real.

Invented, and it inverts the thread. It also dropped the AI accusation entirely,
softening it to a suggestion that the text might be well-written fiction.

The pattern appeared in 3 of 12 briefs. The reference arm never used such a
phrase as a summary verdict, and wrote *"não é unânime"* where threads disagreed.

Other defects: `UAP` expanded to an invented Portuguese phrase; `nightly` left in
English; "that energy of…" rendered as a calque of "that energy". All three source
terms verified present in the fixtures, so these were translation errors rather
than invention.

Did well: sarcasm detected rather than flattened, proper nouns preserved, perfect structural
discipline.

---

# Standing limits

Stated in the rubric before run-001 and unchanged:

- **12 fixtures**, chosen for failure-mode coverage. Can show a model fails;
  cannot establish a pass rate.
- **The judge is not blind**, and Opus is the reference — expect that to flatter
  Opus. The findings above do not depend on it: each was verified against the
  fixture source text, not judged by feel.
- **Naturalness (dimension 1) is not scored here.** Whether the pt-BR sounds
  Brazilian is a native-speaker judgement and belongs to the Owner.
- **One run per fixture**, temp 0.2. A marginal result deserves a re-run.
