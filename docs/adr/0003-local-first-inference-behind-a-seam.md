# Local-first inference behind a swappable seam, settled by a quality gate

Briefs need translation and summarization, which means paying for inference
somewhere. A ChatGPT/Codex subscription does not help — those credits work only
inside Codex and ChatGPT for Excel, never for an API key called programmatically —
so the real choice is a hosted API bill against a local model.

We start local, on Ollama. It costs nothing to run or iterate against, which matters
for a project built for fun. The honest problem is hardware: a 4GB RTX 3050 caps the
practical model near 4B parameters, and pt-BR idiom and sarcastic comment threads
are precisely where small models are weakest. That makes the local choice a genuine
open question rather than a settled one, so `summarizer` is a single narrow
interface that any implementation can sit behind.

## Consequences

An open question left open drifts forever, so it gets a closing date: when the Brief
path ships, ten real threads run through both the local model and Opus 5, compared
side by side, before the choice is committed.

The reference is Opus 5 — the ceiling — on purpose. Compared against a mid-tier
model, a good local result and a weak reference look identical. Against the best
available, a local model that holds up is unambiguously good enough, and one that
does not reveals the true size of the gap, which is the number needed to judge
whether a cheaper hosted tier would close it.
