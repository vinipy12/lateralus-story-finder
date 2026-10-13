# Independent judge verdict — run 004

Date: 2026-08-21

This judgment follows `evals/RUBRIC.md`, not a new preference rubric. I read the
fixtures one at a time across all four arms, then checked disputed claims against
the corresponding fixture JSON. The scores below are **floors**: the worst observed
fixture on each dimension, not averages.

Naturalness is the one explicitly provisional dimension. I can identify concrete
calques, untranslated English, register mixing, and over-written phrasing, but the
Owner's native pt-BR read remains the final authority on whether the voice sounds
Brazilian and works aloud.

## 1. Ranked verdict and ship recommendation

| Rank | Arm | Verdict |
|---:|---|---|
| **1** | **sonnet — claude-sonnet-5** | **Ship this arm.** Gate 0 is 12/12, it handles the hostile thread correctly, covers all eight comments consistently, and has the best factual floor of this run. |
| **2** | **opus — claude-opus-5** | Usually the richest and most controlled prose, but it loses the deciding fixture by turning an ambiguous reaction into a believer. That factual/stance invention matters more than its prose margin. |
| **3** | **haiku — claude-haiku-4-5** | Gate 0 passes, but it invents unrelated UAP/military content, reverses “previously unidentified” into “never identified,” makes attribution errors, and under-covers several threads. Too risky to ship for true-crime material. |
| **4** | **ollama-qwen4b — qwen3.5:4b** | Disqualified at Gate 0: 11/12, with the same invalid-control-character failure on `F02-hostile-thread` as run 003. Its valid outputs also contain repeated factual, attribution, coverage, language, and cap failures. |

**Recommendation: ship Sonnet.** This is not a compromise ranking where Opus wins
quality and Sonnet wins price. On the rubric's floor-based decision rule, Sonnet is
the quality winner too. Opus is often more vivid, but its unsupported stance claim
on the highest-signal fixture is precisely the kind of failure this eval was built
to expose.

The result is still based on 12 deliberately adversarial fixtures and one sample per
fixture. Before making the route permanent, I would re-run Sonnet on at least
`F02-hostile-thread`, `F09-statistics-jargon`, and `F07-link-post` and have
the Owner do the reserved read-aloud pt-BR check. That is a confidence check, not a
reason to prefer another arm on the evidence currently present.

## 2. Per-arm floor scores on the five rubric dimensions

| Arm | Naturalness* | Tone fidelity | Factual fidelity | Discussion coverage | Standalone usefulness |
|---|---:|---:|---:|---:|---:|
| **sonnet** | **4** | **4** | **3** | **4** | **5** |
| **opus** | **4** | **3** | **2** | **4** | **4** |
| **haiku** | **1** | **2** | **1** | **2** | **2** |
| **ollama-qwen4b** | **1** | **1** | **1** | **1** | **1** |

\* Naturalness scores are provisional observations, not a native-speaker verdict.

### Sonnet floors

- **Naturalness — 4.** Generally spoken and readable aloud. The floor comes from
  occasional report-like scaffolding and explanation instead of performance, such
  as glossing a slang term instead of just using it, plus some
  slightly careful phrasing. I found no severe word-order calque or persistent
  untranslated-English pattern.
- **Tone fidelity — 4.** It keeps sarcasm sarcastic, profanity present, and the
  hostile `F02-hostile-thread` thread hostile. It occasionally explains a joke or slang
  term instead of simply landing it, so I would not award an across-the-board 5.
- **Factual fidelity — 3.** Worst instance is `F09-statistics-jargon`: it turns the
  most common error bucket (about a quarter of cases) into "most errors". It also
  inflates "most" classes to "every" class in `F02-hostile-thread`. These are
  real errors, but materially narrower than the inventions in the other arms.
- **Discussion coverage — 4.** All eight comments and disagreements remain
  recognizable throughout. The long drones comment is necessarily compressed and
  loses some of its 14 sub-details, so the floor is 4 rather than 5.
- **Standalone usefulness — 5.** Every valid Brief gives enough context to
  understand the post and discussion without opening Reddit.

### Opus floors

- **Naturalness — 4.** Strong spoken markers and generally fluid narration. Some
  passages are more writerly and performative than ordinary speech, but I found no
  recurring severe calque or untranslated-English defect.
- **Tone fidelity — 3.** It renders the hostility in `F02-hostile-thread` forcefully, but
  the final unsupported claim that a commenter "bought all of it" turns an ambiguous shocked
  reaction into belief. That distorts the thread's stance even while the surrounding
  hostility remains intact.
- **Factual fidelity — 2.** The same `F02-hostile-thread` sentence invents a position for a
  commenter whose entire source text is a stance-free exclamation. On this rubric and subject
  matter, an invented believer in the hostile-thread fixture is close to
  disqualifying. It also inflates “most” lectures to “every” lecture.
- **Discussion coverage — 4.** It consistently uses the available budget and covers
  the substance of all comments. The floor reflects compression of very dense
  material, not wholesale omission.
- **Standalone usefulness — 4.** The briefs are rich and self-contained, but the
  deciding fixture would leave a standalone listener with a false belief about one
  participant's stance.

### Haiku floors

- **Naturalness — 1.** Concrete observations include a literal idiom calque
  ("rabbit hole"), anglicized verbs, English words left untranslated, broken agreement, and
  compressed note-like prose. Those are exactly the rubric's English/calque floor,
  subject to the Owner's final native judgment.
- **Tone fidelity — 2.** It can preserve profanity and obvious sarcasm, including
  the central hostility in `F02-hostile-thread`, but several threads become clipped lists,
  jokes become malformed, and speaker/tone boundaries blur.
- **Factual fidelity — 1.** It inserts UAPs shutting down military sites into the
  unrelated blood-red-sky fixture, invents a 20-year police career, reverses
  “previously unidentified” into “never identified,” and makes several other hard
  errors documented below.
- **Discussion coverage — 2.** Its median discussion is much shorter than Opus or
  Sonnet. It drops multiple comments from `F11-joking-register` and replaces a
  source comment in `F07-link-post` with invented material.
- **Standalone usefulness — 2.** Some briefs stand alone, but the shortest and most
  garbled outputs require source reconstruction or actively mislead the listener.

### Ollama/Qwen floor

- **Naturalness — 1.** Repeated literal syntax, gender/pronoun confusion, corrupted
  words, English slang and profanity left untranslated, anglicized verbs, and calques
  of "it's very much the energy of".
- **Tone fidelity — 1.** Long literal retellings flatten speaker boundaries and
  humor; other outputs omit most of the exchange. The hostile fixture never yields a
  usable Brief at all.
- **Factual fidelity — 1.** Multiple direct inversions and invented attributions are
  summarized below, including the wrong speaker named on a recording and removal of
  every explicit hedge from an allegation the commenter said was probably untrue.
- **Discussion coverage — 1.** `F10-case-writeup` reduces eight comments
  to one question; `F03-short-question` drops the middle of the thread; one fixture is
  a dead tap. Four valid outputs also exceed the discussion cap.
- **Standalone usefulness — 1.** One of 12 taps raises, and several valid outputs
  either omit the post body, put comment material in the body, or leave too little
  discussion to understand the thread.

Gate 0 is separate from these dimension scores: Opus, Sonnet, and Haiku are 12/12;
Qwen is 11/12 and therefore disqualified under the pre-written rubric.

## 3. Factual-error inventory

The original verdict listed each error with the exact conflicting Brief and source
text. That inventory is omitted from the public repository because the source text
is verbatim Reddit content. What remains is the count and the shape of each error.
Omissions are not counted here; they affect coverage, not factual fidelity.

| Arm | Definite factual errors | Shapes |
|---|---:|---|
| **opus** | 2 | an invented stance for a stance-free final comment on `F02-hostile-thread` (the deciding error); "most" inflated to "every" |
| **sonnet** | 2 | the same "most" to "every" inflation; on `F09-statistics-jargon` the most common bucket (about a quarter of cases) described as "most errors" |
| **haiku** | 12 | an invented career length; a commenter's view attributed to the post author; a comment replaced by unrelated invented UAP/military material; two separate anecdotes merged into one speaker; a garment colour moved onto a person; miles converted wrongly to kilometres; a photograph turned into something heard; a collective verdict invented from individual anecdotes; "previously unidentified" reversed to "never identified"; "suspected homicide" collapsed into "homicide"; a population statistic given a status the source never assigned; a conditional possibility stated as fact |
| **ollama-qwen4b** | 26 (on 11 parseable Briefs) | wrong speaker attribution (several); one comment split into two speakers; invented counts and classifications; settings changed (bedroom to living room); the witness who missed an event swapped; every hedge removed from an explicitly doubted allegation; slang abbreviation mistranslated; a date interval contradicted within the same Brief; "stoned" rendered as drunk; question polarity inverted; a specific time made vague; "decedent" rendered as "descendant"; the order of discovery and burial reversed; clothing item changed; the wrong law-enforcement agency named; invented unanimity |

### Prompt-defined proper-name changes, reported separately

Prompt rule 8 says place names stay as written. Every arm rendered at least one
foreign place name as its conventional Portuguese exonym, and two arms translated a
compound place or street name. These are not substantive geographic inventions, so
they did not set the factual ranking, but they are literal violations of the shared
prompt.

### Ambiguous readings not counted as factual errors

Four readings were too close to call: a collective "several agree" backed by one
explicit agreement plus one implicit endorsement (Haiku); an interpretation of a
context-poor comment that the flat feed cannot confirm (Sonnet); a dropped sentence
subject that could mislead but is disambiguated by the previous sentence (Qwen); and
commenter-supplied facts placed in `content_pt` — a provenance error, not an
invention (Haiku).

## 4. Decisive call: `F02-hostile-thread`

All eight source comments were read. In order: an accusation that the story was
written by AI; the author's rebuttal; a challenge to the timeline; the author's
correction; a flat accusation that the story is fabricated; a second, longer
rebuttal from the author; a sarcastic link to another post; and a single shocked
exclamation that takes no position.

Nobody other than the author defends the story. The final comment cannot be promoted
into a believer, and the AI accusation cannot be softened into generic doubt.

| Arm | Call | Evidence |
|---|---|---|
| **sonnet** | **Got it right.** | Preserves the AI accusation, the timeline challenge, the direct fabrication accusation, both of the author's rebuttals and the sarcastic link. It explicitly calls the last reaction neutral and concludes that only the author says the story is real. |
| **haiku** | **Got the required substance right.** | Preserves the AI accusation, the inconsistency, the fabrication accusation, both rebuttals and the sarcasm. It does not explicitly synthesize "only the author", but it invents no supporter. |
| **opus** | **Failed the fixture.** | Its opening correctly says the author is alone, but it later claims the final, stance-free commenter believed the whole story. That is an unsupported believer and contradicts its own correct opening. |
| **ollama-qwen4b** | **Failed structurally.** | No parseable Brief after 382.6 seconds; the same invalid-control-character shape reproduced from run 003. |

This fixture is why Sonnet ranks above Opus. Opus did not fabricate broad consensus,
but the rubric does not require a large invention before factual fidelity matters.
Assigning even one supporter where the source supplies none is a failed
“who said what” reconstruction.

## 5. Quality versus cost

### Check of the proposed token and dollar estimate

The archived prompts establish these exact character counts:

- system prompt: **3,108 characters**;
- user message: **1,719 minimum, 3,265/3,780 middle pair, 11,640 maximum,
  4,445 mean**;
- combined system + user mean: **7,553 characters per Brief**;
- combined output-field characters, mean: **2,739 Opus, 2,655 Sonnet, 1,956
  Haiku** (JSON punctuation adds a little more).

The run archives do not contain provider token-usage metadata, so exact token counts
cannot be recovered from these files. A mixed English/Portuguese planning conversion
of roughly 3.3 characters per input token makes 7,553 characters about 2,290 tokens.
Roughly 2.5 characters per pt-BR output token makes the Opus/Sonnet outputs about
1,060–1,100 tokens. **I therefore agree with the proposed 2,300 input / 1,100 output
estimate for Opus and Sonnet.** It is a reasonable budget, not a measured token bill.

Haiku's actual outputs are about 28% shorter than Sonnet's by character count, so a
uniform 1,100-output-token assumption likely overstates Haiku. A proportional budget
is closer to roughly 780 output tokens. That brevity is not free quality: its
discussion-coverage floor is materially worse.

Using the 2,300/1,100 planning estimate:

| Arm | Approx. per Brief | Approx. at 520 Briefs/year |
|---|---:|---:|
| Opus | **$0.0390** | **$20.28/year** |
| Sonnet, intro rate | **$0.0156** | **$8.11/year** |
| Sonnet, after 2026-08-31 | **$0.0234** | **$12.17/year** |
| Haiku, uniform 1,100-output estimate | **$0.0078** | **$4.06/year** |
| Local Qwen | **$0 marginal API cost** | **$0**, plus machine occupation and waiting |

Using Haiku's observed shorter output proportion instead gives about **$0.0062 per
Brief / $3.23 per year**. This correction does not change the decision.

### Decision

- **Cheapest arm I would actually ship: Sonnet.** Haiku is cheaper, but an unrelated
  UAP/military invention and a reversed identification status are not acceptable
  savings on true-crime material. Local Qwen is not an acceptable arm at any price:
  it fails Gate 0, exceeds caps, takes 113 seconds on average, does not fit the 4 GB
  GPU, and blocks the Owner's machine while the Owner waits.
- **Arm I would ship if cost were no object: Sonnet.** Opus is often more vivid and
  slightly fuller, but this run does not show a positive floor-quality margin over
  Sonnet. It shows the opposite on the decisive hostile thread.
- **What the Opus premium buys:** typically a little more texture and confident
  narration, not better minimum factual reliability in this sample. Against Sonnet
  it costs about **$12/year more during the intro rate** and about **$8/year more
  afterward** under the shared planning estimate. That premium is not justified when
  the more expensive arm is the one that invents a believer on the deciding fixture.
- **What Sonnet buys over Haiku:** explicit speaker separation, correct preservation
  of hostile disagreement, near-complete eight-comment coverage, less broken
  Portuguese, and no unrelated cross-fixture-like invention in the verified sample.
  The incremental annual API cost is roughly **$4–5 during the intro rate** and
  roughly **$8–9 afterward**, depending on whether Haiku's shorter outputs are priced
  from their observed length. That is easily worth it at ten Briefs per week.

At this volume, annual API cost is too small to justify accepting a lower factual
floor. The meaningful trade is trust and tap-to-result experience, not scale.

## 6. What the rubric does not capture well enough

1. **Stance attribution deserves its own explicit criterion.** “Who said what” is
   partly buried across factual fidelity and discussion coverage, but the
   `F02-hostile-thread` result shows it is a first-class product property. With authors and
   threading absent from the model input, the model must preserve position boundaries
   and ambiguity without inventing identity or alignment.

2. **Uncertainty preservation should be scored explicitly.** Qwen turns a
   commenter's explicitly doubted allegation into a flat fact. In true-crime material, removing a
   hedge from an allegation can be as damaging as inventing a name or date.

3. **Body-versus-discussion provenance matters.** Haiku and Qwen sometimes move a
   commenter's assertion into `content_pt`. The claim may exist somewhere in the
   input, but a listener can no longer tell whether it came from the post or from a
   commenter. That should be a scored attribution error.

4. **“Conte TUDO” is not literally compatible with a hard message budget.** The
   rubric should ask for all material positions and all salient unique details, then
   define what may be compressed. Counting omitted low-value details the same as
   dropping a disagreement would reward length rather than judgment.

5. **Cap compliance belongs beside Gate 0.** A parseable Brief that exceeds the
   Telegram/product cap still cannot be shipped as-is. Qwen has four over-cap outputs;
   that is a contract failure even though only one output fails the current Gate 0
   definition. Code must still enforce sentence-boundary truncation because every
   run has shown prompt-only length control is unreliable.

6. **Interactive latency has more product weight here than “latency, last” implies.**
   The rubric correctly puts fidelity first, but 113 seconds while occupying a
   machine that cannot fit the model on its GPU is not merely a cold-start metric.
   It is the Owner's wait on every lazy tap. For an otherwise equal local arm, that
   would materially affect usefulness.

7. **The naturalness gate needs an Owner receipt.** Mechanical spoken markers can
   catch formal language, but they cannot prove that slang is earned, rhythm works
   aloud, or the voice sounds Brazilian. The final route should record the Owner's
   read-aloud verdict rather than treating this judge's provisional 1–5 number as
   authoritative.

8. **One generation per fixture establishes a failure, not reliability.** A hard
   failure is evidence against an arm; a clean 12/12 is not a stable pass-rate
   estimate. The winner should be re-run on the highest-risk fixtures, and a future
   release gate should retain repeat trials for factual-floor cases.

9. **The fixtures do not exercise Portuguese source pass-through.** The manifest
   already identifies this gap. A shipped prompt still has an untested rule 10.

10. **Self-report integrity should not be part of model quality, but it should shape
    eval operations.** The discarded Haiku attempt shows that run provenance,
    prompt hashes, input manifests, and mechanical validation must remain external to
    the model. The verified run-004 Haiku arm is legitimate; the lesson is to trust
    artifacts, not an arm's own claim that it ran cleanly.

Final call: **Sonnet is the only arm in run 004 that combines Gate 0 success with an
acceptable factual floor and a correct decisive hostile-thread reconstruction. Ship
Sonnet, subject to the Owner's native pt-BR read-aloud check and a focused repeat run
for variance.**
