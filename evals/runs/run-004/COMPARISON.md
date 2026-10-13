# Translation eval — side by side

Score with `evals/RUBRIC.md` open. Judge one fixture across both arms
before moving to the next; do not read one arm end to end first.

Arms: `opus` (claude-opus-5), `sonnet` (claude-sonnet-5), `haiku` (claude-haiku-4-5), `ollama-qwen4b` (local qwen3.5:4b).

## Gate 0 — structural validity

| Fixture | opus | sonnet | haiku | ollama-qwen4b |
|---|---|---|---|---|
| `F01-long-narrative` | pass | pass | pass | pass |
| `F07-link-post` | pass | pass | pass | pass |
| `F02-hostile-thread` | pass | pass | pass | **FAIL** — invalid JSON: Invalid control character at: line 3 column 10895 (char 10968) |
| `F04-short-question-profane` | pass | pass | pass | pass |
| `F03-short-question` | pass | pass | pass | pass |
| `F05-sarcasm-empty-body` | pass | pass | pass | pass |
| `F06-image-post` | pass | pass | pass | pass |
| `F12-anecdotal-thread` | pass | pass | pass | pass |
| `F10-case-writeup` | pass | pass | pass | pass |
| `F11-joking-register` | pass | pass | pass | pass |
| `F09-statistics-jargon` | pass | pass | pass | pass |
| `F08-forensic-jargon` | pass | pass | pass | pass |

**opus** — {"arm": "opus", "model": "claude-opus-5", "fixtures": 12, "valid_briefs": 12, "failures": 0}

**sonnet** — {"arm": "sonnet", "model": "claude-sonnet-5", "fixtures": 12, "valid_briefs": 12, "failures": []}

**haiku** — {"arm": "haiku", "model": "claude-haiku-4-5", "fixtures": 12, "valid_briefs": 12, "failures": 0}

**ollama-qwen4b** — {"arm": "ollama", "model": "qwen3.5:4b", "fixtures": 12, "valid_briefs": 11, "failures": 1, "total_seconds": 1358.1, "mean_seconds": 113.2}


---

_Per-fixture outputs omitted from the public repository: they are translations of real Reddit threads. Only the structural results above are kept._
