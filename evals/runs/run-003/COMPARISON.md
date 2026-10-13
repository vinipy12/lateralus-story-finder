# Translation eval — side by side

Score with `evals/RUBRIC.md` open. Judge one fixture across both arms
before moving to the next; do not read one arm end to end first.

`ollama` = qwen3.5:4b, local. `opus` = claude-opus-5, the reference.

## Gate 0 — structural validity

| Fixture | ollama | opus |
|---|---|---|
| `F01-long-narrative` | pass | pass |
| `F07-link-post` | pass | pass |
| `F02-hostile-thread` | **FAIL** — invalid JSON: Invalid control character at: line 3 column 10758 (char 10831) | pass |
| `F04-short-question-profane` | pass | pass |
| `F03-short-question` | pass | pass |
| `F05-sarcasm-empty-body` | pass | pass |
| `F06-image-post` | pass | pass |
| `F12-anecdotal-thread` | pass | pass |
| `F10-case-writeup` | pass | pass |
| `F11-joking-register` | pass | pass |
| `F09-statistics-jargon` | **FAIL** — discussion_pt is not a string | pass |
| `F08-forensic-jargon` | pass | pass |

**ollama** — {"arm": "ollama", "model": "qwen3.5:4b", "fixtures": 12, "valid_briefs": 10, "failures": 2, "total_seconds": 944.7, "mean_seconds": 78.7}

**opus** — {"arm": "opus", "model": "claude-opus-5", "fixtures": 12, "valid_briefs": 12, "failures": 0}


---

_Per-fixture outputs omitted from the public repository: they are translations of real Reddit threads. Only the structural results above are kept._
