# The shared summarizer prompt

Both arms of the translation eval send **exactly this prompt**. Changing it for one
model and not the other turns a model comparison into a prompt comparison, which is
not the question ADR-0003 asks.

If a prompt change is needed, change it for both arms and re-run both. The runs are
cheap; a comparison nobody can trust is not.

## System prompt

```
Você conta histórias do Reddit em português brasileiro FALADO.

O que você escreve vai ser LIDO EM VOZ ALTA para outras pessoas — pense em
alguém narrando isso num vídeo curto. Se a frase é chata de falar, ela está
errada. Leia cada frase em voz alta na sua cabeça antes de escrever.

Regras:

1. Escreva como se fala, não como se escreve. Frases curtas, uma ideia por
   frase. Pode começar frase com "E", "Mas", "Aí", "Só que", "Daí". Português
   correto demais soa como robô lendo relatório — não é isso que a gente quer.

2. Troque as formas escritas pelas faladas. Use SEMPRE a coluna da direita:

   está → tá          estão → tão        para o/a → pro/pra
   afirmou → disse    declarou → falou   relatou → contou
   posteriormente → depois               anteriormente → antes
   aproximadamente → uns                 atualmente → hoje
   residência → casa                     indivíduo → cara, pessoa
   realizar → fazer                      obter → conseguir
   entretanto/todavia/no entanto → só que, mas
   além disso/ademais → e tem mais, e ainda
   portanto/por conseguinte → então      bastante → muito, bem

3. Estão PROIBIDAS estas expressões: "cabe ressaltar", "vale destacar", "é
   importante notar", "vale lembrar", "em suma", "por fim", "outrossim", "no
   que tange", "o referido", "supracitado", "diante do exposto", "de modo geral".

4. NUNCA invente concordância. Está proibido escrever "a maioria concorda",
   "todos concordam", "o consenso é", "a comunidade reage", "a comunidade
   acha", "os usuários em geral", "no geral, o pessoal acha" ou qualquer
   variação. Não termine com uma frase que resume o que "a comunidade" pensa.
   Threads raramente pensam uma coisa só.

5. Diga quem falou o quê. "Um cara acusa X, aí a autora responde Y." Se só o
   autor do post defende a versão dele e o resto duvida, fala isso com todas as
   letras. Briga é briga; acusação é acusação, não é "sugestão".

6. Conte TUDO. Não deixe comentário de fora, não corte detalhe. Quem escuta não
   vai abrir o post — se você não contar, a pessoa não fica sabendo. Falar
   informal não é falar menos.

7. Preserve o tom. Thread engraçado tem que ser engraçado, thread pesado tem que
   ser pesado. Não amenize, não moralize, não suavize palavrão.

8. Não invente nada. Nomes, datas, lugares, números e termos técnicos ficam como
   estão; nome próprio e nome de lugar não se traduz. Se não souber o que uma
   sigla quer dizer, deixa a sigla quieta — não chute o significado. Se o
   material for ambíguo, deixa ambíguo.

9. Não deixe palavra nenhuma em inglês.

10. Se o material já estiver em português, conta sem traduzir.

Responda APENAS com um objeto JSON válido, sem cercas de código e sem comentários:

{
  "title_pt": "o título do post, em português falado",
  "content_pt": "o que o post conta, em português falado, ou null se não houver corpo",
  "discussion_pt": "o que rolou na discussão, em português falado"
}

Limites de tamanho:
- discussion_pt: no máximo 2400 caracteres
- content_pt: no máximo 1200 caracteres

Use o espaço. Briefing curto demais deixa quem escuta sem entender.
```

## User message

Built per fixture:

```
Comunidade: r/{subreddit}
Título: {title}

Corpo do post:
{selftext or "(sem corpo — post de link ou imagem)"}

Comentários:
{for each comment: "- {body}"}
```

## Why these rules

Each one targets a way the eval is expected to break:

| Rule | Failure it is aimed at |
|---|---|
| 1 — write spoken, not written | Both arms produced correct, bloated written Portuguese. A Brief is meant to be read aloud |
| 2 — the swap table | The concrete half of rule 1. "Write casually" is a judgement; a word list is a lookup |
| 3 — banned formal phrases | The connective tissue of written Portuguese, which survives even when the vocabulary is casual |
| 4 — never invent agreement | The run-001 failure. Now includes the "a comunidade reage" phrasing that survived run-002 |
| 5 — attribute by name | The other half of the same failure: naming who said what makes fabrication harder than a vague summary |
| 6 — tell everything | The run-002 under-fill: 5 of 12 local briefs used under two-thirds of the budget. States explicitly that informal ≠ shorter |
| 7 — preserve tone | Small models flatten sarcasm into earnest description, and soften profanity |
| 8 — no invention, keep unknown acronyms | Hallucination, which on true-crime material is not cosmetic; run-001 and run-002 both invented a `UAP` expansion |
| 9 — no English left in | run-001 left `nightly` untranslated |
| 10 — Portuguese passes through | Spec requires it; also catches a model that "translates" pt to pt and degrades it |

## Revision history

**run-004 (2026-08-21) — the cap is raised, and `content_pt` gets one.**

Run-003 established that rule 6 ("conte TUDO") and a 1500-char cap are in direct
conflict at eight comments: the reference arm overran on **every** substantive
fixture by 200-650 chars on first draft, and eleven of its twelve finals sat
pinned at 1412-1500 — meaning detail was being cut by the budget, not by
judgement. On `F11-joking-register` it dropped 6 of 14 listed anomalies.

New limits, derived from the real constraint rather than picked:

| | limit | why |
|---|---|---|
| `discussion_pt` | **2400** | was 1500 |
| `content_pt` | **1200** | had **no cap at all** |

Telegram caps a message at 4096 characters and the spec requires one Brief to fit
one message. Budget: title ~120 + `content_pt` 1200 + `discussion_pt` 2400 = 3720,
leaving ~370 for the permalink, labels and formatting. It fits with margin.

`content_pt` previously being uncapped was a latent bug, not a nicety — run-003's
reference arm wrote a **9,427-character** `content_pt` on `F02-hostile-thread`,
which alone is more than twice a whole Telegram message. The local model tried to
reproduce the 10k body nearly verbatim and emitted invalid JSON doing it.

**This does not make the cap a prompt concern.** Three runs have now failed to
control length by instruction, in both directions. Code must hard-cap and
truncate at a sentence boundary, as the spec already requires. The raise is about
giving the *content* room, not about trusting the model to respect a number.

**run-003 (2026-08-21) — register change, on Owner feedback.**

The Owner's verdict on run-002: Opus is clearly better on accent, but **both
arms are "bloated and too correct"**. The target is a Brief someone can read
aloud to other people — think narrating a short video. All the detail, none of
the formality.

This is a register change, not a quality change, and it explains the bloat:
both arms were writing *written* Portuguese for something meant to be *spoken*.

Applying what run-002 established — **this model follows enumerated patterns,
not self-assessments** — the change is deliberately mechanical rather than
impressionistic:

- **A swap table (rule 2), not an instruction to "be casual."** `está → tá`,
  `afirmou → disse`, `posteriormente → depois`. A lookup, not a judgement.
- **A banned-phrase list (rule 3)** for the connectives that make prose sound
  like a report — *cabe ressaltar*, *em suma*, *no que tange*. Vocabulary can
  go casual while this scaffolding keeps the register formal.
- **The read-aloud test up front**, before the rules, as the frame everything
  else serves.

Two run-002 defects are folded into the same revision, since both arms are
re-running anyway:

- Rule 4's banned list gains *"a comunidade reage"* and *"a comunidade acha"* —
  the collective voice survived run-002 in words the previous list did not
  enumerate.
- Rule 6 now says **"Conte TUDO… Falar informal não é falar menos"**, targeting
  the under-fill directly. Informality invites compression, and the local arm
  was already producing briefs at under two-thirds of budget.

**Risk accepted:** rule 6 pushes for length while the register change pushes for
brevity, and run-002 already overran the cap on 4 of 12. The cap belongs in code
regardless — the spec requires a hard cap truncated at a sentence boundary — so
overrun is measured here, not prevented by prompt.

**run-002 (2026-08-21)** — the anti-consensus rule was promoted from 5th to
1st and made concrete, and a new rule 2 asks for named attribution.

In run-001 the rule read only *"Quando os comentários discordarem entre si, diga
isso. Não invente consenso."* `qwen3.5:4b` ignored it in 3 of 12 briefs, and on
`F02-hostile-thread` closed a hostile thread with *"A maioria concorda que a
experiência foi terrível e que o caso é real"* — inverting a thread where nobody
but the author believed the story. See `RESULTS.md`.

Three things changed, each aimed at a specific mechanism:

- **Position.** It was 5th of 7, buried mid-list. Salience is scarce for a 4B
  model, so the rule that failed goes first.
- **Banned strings rather than a principle.** "Não invente consenso" requires the
  model to recognize that a sentence it is about to write constitutes invented
  consensus. Naming the actual phrases — *a maioria concorda*, *todos concordam*,
  *o consenso é* — is a pattern match, which is far easier.
- **The failure shape, named.** Run-001's invention arrived as a *closing
  conciliatory sentence*, so the rule now forbids ending that way specifically.

Rule 6 also gained "keep the acronym if unsure", targeting the invented `UAP`
expansion.

**A prompt change invalidates cross-run comparison.** Both arms must be re-run
together; run-001 output was archived separately and is not comparable
to anything produced under this version.

The JSON requirement is deliberate and is itself under test. The spec has
`summarizer` returning a **validated** `Brief`, so malformed output fails loudly at
the boundary rather than reaching the chat. A model that cannot reliably emit the
shape is disqualified regardless of how good its prose is — record that as a result
rather than working around it with a lenient parser.
