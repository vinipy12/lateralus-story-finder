"""The measurement, shared by every API arm.

`build_prompt.py` exists because two arms building prompts separately drift, and
a drifted prompt turns a model comparison into a prompt comparison. This module
is the same argument applied one level out: two arms *measuring* separately
drift, and a drifted measurement turns a model comparison into a harness
comparison.

That is not hypothetical here. Runs 001-007 compared Claude arms that went
through an agent harness — file access, unlimited revisions, "2-6 rounds of
trimming to land under budget" — against Codex and Ollama arms called once and
parsed as-is. The prompts were identical and verified. The comparison was still
not a comparison, and the arm with the revise loop won on the dimension the
revise loop most directly affects.

So the loop lives here, once, and an arm supplies only a `call` function. An arm
cannot quietly get a second attempt, because there is nowhere for it to put one.

Production shape is one shot: `summarizer` returns a validated `Brief` from a
single call. Every arm measured through this module is measured in that shape.
"""

import json
import os
import time
from pathlib import Path
from typing import Callable, Protocol

from build_prompt import SYSTEM_PROMPT, build_user_message, load_fixtures

DISCUSSION_CAP = 2400
CONTENT_CAP = 1200


class Caller(Protocol):
    """One model turn. Returns (text, error, usage).

    `error` is transport-level only — a timeout, a refused request, a bad model
    id. Anything the model actually said comes back as `text` and is judged.
    """

    def __call__(self, system: str, user: str, timeout: float) -> tuple[str, str | None, dict | None]:
        ...


def load_env_file(path: Path = Path(".env")) -> None:
    """Populate os.environ from .env, without overriding what is already set.

    The project keeps credentials in .env (see `story_finder.config`), but these
    runners are standalone scripts rather than the app, so nothing loads it for
    them. Explicit environment always wins, so exporting a key for one run does
    what it looks like it does.
    """
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        os.environ.setdefault(key, value)


def extract_json(raw: str) -> tuple[dict | None, str | None]:
    """Pull the Brief object out of whatever the model returned.

    Copied byte-for-byte from `run_codex.py` rather than improved, so an API arm
    is not accidentally held to a different standard than the CLI arm it is being
    compared against. The scan-backwards approach is transport handling for
    `codex exec`'s transcript output; an API reply is usually the object alone
    and hits the first attempt. Keeping it identical costs nothing and removes a
    variable.
    """
    text = raw.strip()
    start = text.rfind("{")
    while start != -1:
        candidate = text[start:]
        end = candidate.rfind("}")
        if end != -1:
            try:
                parsed = json.loads(candidate[: end + 1])
                if isinstance(parsed, dict) and "discussion_pt" in parsed:
                    return parsed, None
            except json.JSONDecodeError:
                pass
        start = text.rfind("{", 0, start)
    return None, "no parseable Brief object in output"


def validate(brief: dict) -> tuple[str | None, str | None]:
    """Return (structural_error, cap_violation) — deliberately separate.

    Gate 0a (structural validity) and Gate 0b (cap compliance) are different
    failures with different remedies. A malformed Brief raises in production and
    nothing can be salvaged. An over-cap Brief is real, judgeable prose that code
    truncates at a sentence boundary, as the spec already requires.

    Collapsing them discards the output — which is what an earlier version of
    `run_codex.py` did, losing every over-cap Brief before it could be read.
    """
    for key in ("title_pt", "discussion_pt"):
        if key not in brief:
            return f"missing required field: {key}", None
        if not isinstance(brief[key], str) or not brief[key].strip():
            return f"{key} is not a non-empty string", None

    violations = []
    if len(brief["discussion_pt"]) > DISCUSSION_CAP:
        violations.append(f"discussion_pt {len(brief['discussion_pt'])}/{DISCUSSION_CAP}")
    content = brief.get("content_pt")
    if content is not None and len(content) > CONTENT_CAP:
        violations.append(f"content_pt {len(content)}/{CONTENT_CAP}")
    return None, ("over cap: " + ", ".join(violations)) if violations else None


def run_arm(
    call: Caller,
    *,
    model: str,
    arm: str,
    fixtures_dir: Path,
    out_dir: Path,
    timeout: float,
) -> int:
    """Every fixture, once each, recorded whether it succeeded or not.

    No retries, no revision, no second look. A failure is data — the local model
    failing `LetsNotMeet` twice on an unescaped control character is one of the
    more useful findings this eval has produced, and it only exists because
    nothing retried around it.
    """
    fixtures = load_fixtures(fixtures_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = []

    for index, fixture in enumerate(fixtures, start=1):
        user = build_user_message(fixture)
        name = f"{fixture['subreddit']}-{fixture['id']}"
        print(f"[{index}/{len(fixtures)}] {name}", flush=True)
        started = time.monotonic()

        raw, error, usage = call(SYSTEM_PROMPT, user, timeout)
        brief, cap_violation = None, None
        if not error:
            brief, error = extract_json(raw)
            if brief is not None:
                error, cap_violation = validate(brief)
                if error:
                    brief = None

        elapsed = time.monotonic() - started
        record = {
            "fixture": name,
            "subreddit": fixture["subreddit"],
            "exercises": fixture.get("exercises"),
            "model": model,
            "arm": arm,
            "seconds": round(elapsed, 1),
            "prompt_chars": len(user),
            "brief": brief,
            "error": error,
            "cap_violation": cap_violation,
            "usage": usage,
            "raw": raw[-4000:] if error else None,
        }
        (out_dir / f"{name}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary.append(record)
        status = (
            "FAILED — " + str(error)
            if not brief
            else ("ok" if not cap_violation else "ok, " + cap_violation)
        )
        print(f"    {elapsed:.0f}s  {status}", flush=True)

    ok = sum(1 for r in summary if r["brief"])
    capped = sum(1 for r in summary if r.get("cap_violation"))
    total = sum(r["seconds"] for r in summary)
    tokens_in = sum((r["usage"] or {}).get("input_tokens", 0) for r in summary)
    tokens_out = sum((r["usage"] or {}).get("output_tokens", 0) for r in summary)
    (out_dir / "SUMMARY.json").write_text(
        json.dumps(
            {
                "arm": arm,
                "model": model,
                "fixtures": len(summary),
                "valid_briefs": ok,
                "failures": len(summary) - ok,
                "over_cap": capped,
                "total_seconds": round(total, 1),
                "mean_seconds": round(total / len(summary), 1) if summary else 0,
                "input_tokens": tokens_in,
                "output_tokens": tokens_out,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n{ok}/{len(summary)} structurally valid, {capped} over cap, {total:.0f}s total")
    print(f"tokens: {tokens_in} in, {tokens_out} out")
    return 0 if ok == len(summary) else 1


def add_common_args(parser, *, default_model: str) -> None:
    parser.add_argument("--model", default=default_model)
    parser.add_argument("--fixtures", default=Path("evals/fixtures"), type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--timeout", default=600.0, type=float)
    parser.add_argument(
        "--max-tokens",
        default=16000,
        type=int,
        help="Ceiling only. A Brief is ~1,500 tokens; this exists so a runaway "
        "generation fails loudly instead of billing indefinitely.",
    )
