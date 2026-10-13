"""Run every fixture through a Codex CLI model.

Mirrors run_ollama.py so the arms stay comparable: same shared prompt, same
strict parse, failures recorded as failures rather than retried around.

Unlike the Claude arms — which went through an agent harness that reads files
and writes JSON itself — this calls the model directly with the prompt and
takes what comes back, exactly as the Ollama arm does. Worth remembering when
comparing: an agent harness can recover from a malformed first attempt, a
direct call cannot.

Usage:
    python3 evals/run_codex.py --model gpt-5.6-sol --out evals/runs/run-006/sol
"""

import argparse
import json
import subprocess
import time
from pathlib import Path

from build_prompt import SYSTEM_PROMPT, build_user_message, load_fixtures


def call_codex(model: str, system: str, user: str, timeout: float) -> tuple[str, str | None]:
    """One non-interactive Codex turn. Returns (text, error)."""
    prompt = (
        f"{system}\n\n"
        "---\n\n"
        "Abaixo está o material. Responda APENAS com o objeto JSON pedido acima.\n"
        "Não use ferramentas, não leia arquivos, não escreva arquivos.\n\n"
        f"{user}"
    )
    try:
        proc = subprocess.run(
            ["codex", "exec", "--skip-git-repo-check", "-m", model, prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "", f"timeout after {timeout}s"
    if proc.returncode != 0:
        return proc.stdout, f"codex exit {proc.returncode}: {proc.stderr.strip()[:200]}"
    return proc.stdout, None


def extract_json(raw: str) -> tuple[dict | None, str | None]:
    """Pull the Brief object out of Codex's transcript output.

    `codex exec` prints a session header and event lines around the reply, so
    unlike the Ollama arm the payload has to be located rather than parsed
    whole. Locating it is transport handling; the strictness below is the
    actual test.
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
    this file did, losing every over-cap Brief before it could be read.
    """
    for key in ("title_pt", "discussion_pt"):
        if key not in brief:
            return f"missing required field: {key}", None
        if not isinstance(brief[key], str) or not brief[key].strip():
            return f"{key} is not a non-empty string", None

    violations = []
    if len(brief["discussion_pt"]) > 2400:
        violations.append(f"discussion_pt {len(brief['discussion_pt'])}/2400")
    content = brief.get("content_pt")
    if content is not None and len(content) > 1200:
        violations.append(f"content_pt {len(content)}/1200")
    return None, ("over cap: " + ", ".join(violations)) if violations else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--fixtures", default="evals/fixtures", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--timeout", default=600.0, type=float)
    args = parser.parse_args()

    fixtures = load_fixtures(args.fixtures)
    args.out.mkdir(parents=True, exist_ok=True)
    summary = []

    for index, fixture in enumerate(fixtures, start=1):
        user = build_user_message(fixture)
        name = f"{fixture['subreddit']}-{fixture['id']}"
        print(f"[{index}/{len(fixtures)}] {name}", flush=True)
        started = time.monotonic()

        raw, error = call_codex(args.model, SYSTEM_PROMPT, user, args.timeout)
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
            "model": args.model,
            "arm": args.out.name,
            "seconds": round(elapsed, 1),
            "prompt_chars": len(user),
            "brief": brief,
            "error": error,
            "cap_violation": cap_violation,
            "raw": raw[-4000:] if error else None,
        }
        (args.out / f"{name}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        summary.append(record)
        status = "FAILED — " + str(error) if not brief else ("ok" if not cap_violation else "ok, " + cap_violation)
        print(f"    {elapsed:.0f}s  {status}", flush=True)

    ok = sum(1 for r in summary if r["brief"])
    capped = sum(1 for r in summary if r.get("cap_violation"))
    total = sum(r["seconds"] for r in summary)
    (args.out / "SUMMARY.json").write_text(
        json.dumps(
            {
                "arm": args.out.name,
                "model": args.model,
                "fixtures": len(summary),
                "valid_briefs": ok,
                "failures": len(summary) - ok,
                "over_cap": capped,
                "total_seconds": round(total, 1),
                "mean_seconds": round(total / len(summary), 1),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n{ok}/{len(summary)} structurally valid, {capped} over cap, {total:.0f}s total")


if __name__ == "__main__":
    main()
