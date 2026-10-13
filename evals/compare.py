"""Render both arms of the translation eval side by side for judging.

Reads evals/runs/<arm>/ and writes a single Markdown document with the two
outputs for each fixture adjacent, in the order the rubric says to judge them:
one fixture at a time, both arms together. Comparative judgement is far more
reliable than remembered absolute judgement, and reading one whole arm and then
the other guarantees the latter.

Usage:
    python3 evals/compare.py [--out evals/runs/COMPARISON.md]
"""

import argparse
import json
from pathlib import Path

ARMS = ("opus", "sonnet", "haiku", "ollama-qwen4b")


def load_arm(directory: Path) -> dict[str, dict]:
    if not directory.is_dir():
        return {}
    return {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(directory.glob("*.json"))
        if p.name != "SUMMARY.json"
    }


def field(record: dict | None, name: str) -> str:
    """One Brief field, or an honest marker for why it is missing."""
    if record is None:
        return "_(arm produced no record for this fixture)_"
    if record.get("error"):
        return f"**STRUCTURAL FAILURE** — {record['error']}"
    brief = record.get("brief") or {}
    value = brief.get(name)
    if value is None:
        return "_(null)_"
    text = str(value).strip()
    return text if text else "_(empty string)_"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", default="evals/runs", type=Path)
    parser.add_argument("--fixtures", default="evals/fixtures", type=Path)
    parser.add_argument("--out", default="evals/runs/COMPARISON.md", type=Path)
    args = parser.parse_args()

    arms = {arm: load_arm(args.runs / arm) for arm in ARMS}
    names = sorted(set().union(*(a.keys() for a in arms.values())) if any(arms.values()) else [])
    if not names:
        raise SystemExit(f"no arm output found under {args.runs}")

    lines: list[str] = [
        "# Translation eval — side by side",
        "",
        "Score with `evals/RUBRIC.md` open. Judge one fixture across both arms",
        "before moving to the next; do not read one arm end to end first.",
        "",
        "Arms: `opus` (claude-opus-5), `sonnet` (claude-sonnet-5), `haiku` (claude-haiku-4-5), `ollama-qwen4b` (local qwen3.5:4b).",
        "",
    ]

    # Gate 0 first — structural validity decides before prose is discussed.
    lines += [
        "## Gate 0 — structural validity",
        "",
        "| Fixture | " + " | ".join(ARMS) + " |",
        "|---" * (len(ARMS) + 1) + "|",
    ]
    for name in names:
        cells = []
        for arm in ARMS:
            record = arms[arm].get(name)
            if record is None:
                cells.append("missing")
            elif record.get("error"):
                cells.append(f"**FAIL** — {record['error']}")
            else:
                cells.append("pass")
        lines.append(f"| `{name}` | " + " | ".join(cells) + " |")

    for arm in ARMS:
        summary = args.runs / arm / "SUMMARY.json"
        if summary.is_file():
            data = json.loads(summary.read_text(encoding="utf-8"))
            lines += ["", f"**{arm}** — {json.dumps(data, ensure_ascii=False)}"]

    lines += ["", "---", ""]

    for name in names:
        records = {arm: arms[arm].get(name) for arm in ARMS}
        reference = next((r for r in records.values() if r), {})
        exercises = reference.get("exercises") or "—"

        fixture_path = args.fixtures / f"{name}.json"
        source = json.loads(fixture_path.read_text(encoding="utf-8")) if fixture_path.is_file() else {}

        lines += [
            f"## {name}",
            "",
            f"**Exercises:** {exercises}",
            "",
            f"**Original title:** {source.get('title', '—')}",
            "",
            f"**Body:** {len(source.get('selftext') or '')} chars · "
            f"**Comments:** {len(source.get('comments') or [])} · "
            f"[thread]({source.get('permalink', '')})",
            "",
        ]

        for label, key in (("Título", "title_pt"), ("Corpo", "content_pt"), ("Discussão", "discussion_pt")):
            lines += [f"### {label}", ""]
            for arm in ARMS:
                lines += [f"**{arm}**", "", field(records[arm], key), ""]

        seconds = (records.get("ollama-qwen4b") or {}).get("seconds")
        if seconds is not None:
            lines += [f"_ollama: {seconds}s_", ""]
        lines += ["---", ""]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out} — {len(names)} fixtures")


if __name__ == "__main__":
    main()
