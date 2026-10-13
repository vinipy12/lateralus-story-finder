"""Run every fixture through the local Ollama model.

One arm of the translation eval. The other arm sends the identical prompt to
Opus 5. Opus is the reference deliberately: comparing against a mid-tier model
would leave a good local result indistinguishable from a weak reference
(ADR-0003).

Usage:
    python3 evals/run_ollama.py [--model qwen3.5:4b] [--out evals/runs/ollama]

Writes one JSON per fixture plus a run summary. Records failures as failures —
a model that cannot emit valid JSON is disqualified by the spec's boundary
validation, so that outcome is data, not something to paper over.
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from build_prompt import SYSTEM_PROMPT, build_user_message, load_fixtures

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "qwen3.5:4b"


def call_ollama(host: str, model: str, system: str, user: str, timeout: float) -> dict:
    payload = {
        "model": model,
        "system": system,
        "prompt": user,
        "stream": False,
        # qwen3.5 is thinking-capable and thinks by default. Left on, it spends
        # minutes per fixture emitting a reasoning trace and then wraps the JSON
        # in it, which fails the parser. The product taps a Brief and edits a
        # placeholder message — a reasoning budget buys nothing the Owner sees.
        "think": False,
        # Low temperature: we are measuring capability, not sampling variance.
        "options": {"temperature": 0.2, "num_ctx": 8192},
    }
    request = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def parse_brief(raw: str) -> tuple[dict | None, str | None]:
    """Parse the model's output into a Brief, or explain why it is not one.

    Deliberately strict about structure and forgiving only of code fences, which
    are a formatting habit rather than a comprehension failure. Anything else
    that fails here would also fail Pydantic validation in production.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1] if "```" in text[3:] else text[3:]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"

    if not isinstance(parsed, dict):
        return None, f"expected an object, got {type(parsed).__name__}"

    missing = [k for k in ("title_pt", "discussion_pt") if k not in parsed]
    if missing:
        return None, f"missing required field(s): {', '.join(missing)}"
    if not isinstance(parsed.get("title_pt"), str):
        return None, "title_pt is not a string"
    if not isinstance(parsed.get("discussion_pt"), str):
        return None, "discussion_pt is not a string"

    return parsed, None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--fixtures", default="evals/fixtures", type=Path)
    parser.add_argument("--out", default="evals/runs/ollama", type=Path)
    parser.add_argument("--timeout", default=600.0, type=float)
    args = parser.parse_args()

    fixtures = load_fixtures(args.fixtures)
    if not fixtures:
        raise SystemExit(f"no fixtures found in {args.fixtures}")

    args.out.mkdir(parents=True, exist_ok=True)
    summary = []

    for index, fixture in enumerate(fixtures, start=1):
        user = build_user_message(fixture)
        started = time.monotonic()
        print(f"[{index}/{len(fixtures)}] {fixture['subreddit']}/{fixture['id']}", flush=True)

        try:
            response = call_ollama(
                args.host, args.model, SYSTEM_PROMPT, user, args.timeout
            )
            raw = response.get("response", "")
            error = None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raw, error = "", f"request failed: {exc}"

        elapsed = time.monotonic() - started
        brief, parse_error = (None, error) if error else parse_brief(raw)

        record = {
            "fixture": f"{fixture['subreddit']}-{fixture['id']}",
            "subreddit": fixture["subreddit"],
            "exercises": fixture.get("exercises"),
            "model": args.model,
            "arm": "ollama",
            "seconds": round(elapsed, 1),
            "prompt_chars": len(user),
            "brief": brief,
            "error": parse_error,
            "raw": raw if parse_error else None,
        }
        (args.out / f"{record['fixture']}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary.append(record)

        status = "ok" if brief else f"FAILED — {parse_error}"
        print(f"    {elapsed:.0f}s  {status}", flush=True)

    ok = sum(1 for r in summary if r["brief"])
    total_seconds = sum(r["seconds"] for r in summary)
    (args.out / "SUMMARY.json").write_text(
        json.dumps(
            {
                "arm": "ollama",
                "model": args.model,
                "fixtures": len(summary),
                "valid_briefs": ok,
                "failures": len(summary) - ok,
                "total_seconds": round(total_seconds, 1),
                "mean_seconds": round(total_seconds / len(summary), 1),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n{ok}/{len(summary)} valid briefs, {total_seconds:.0f}s total")


if __name__ == "__main__":
    main()
