#!/usr/bin/env python3
"""Validate the repository shell and committed Lateralus project identity."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import NoReturn


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = (
    Path("README.md"),
    Path("LICENSE"),
    Path(".github/workflows/repo-integrity.yml"),
)
PROJECT_FILE = Path(".lateralus/project.json")
EXPECTED_PROJECT = {
    "project_id": "lateralus-story-finder",
    "github_repo": "vinipy12/lateralus-story-finder",
}


class DuplicateKeyError(ValueError):
    """Raised when a JSON object repeats a key."""


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key: {key}")
        result[key] = value
    return result


def fail(message: str) -> NoReturn:
    print(f"repo-integrity: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_required_files() -> None:
    for relative_path in REQUIRED_FILES:
        path = REPOSITORY_ROOT / relative_path
        if not path.is_file() or path.stat().st_size == 0:
            fail(f"required file is missing or empty: {relative_path}")


def validate_project_identity() -> None:
    path = REPOSITORY_ROOT / PROJECT_FILE
    try:
        project = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except FileNotFoundError:
        fail(f"project identity is missing: {PROJECT_FILE}")
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as error:
        fail(f"project identity is malformed: {PROJECT_FILE}: {error}")

    if not isinstance(project, dict):
        fail(f"project identity must be a JSON object: {PROJECT_FILE}")

    for key, value in project.items():
        if not isinstance(value, str) or not value:
            fail(f"project identity value must be a non-empty string: {key}")

    if project != EXPECTED_PROJECT:
        fail(
            "project identity must contain exactly the expected project_id and "
            f"github_repo values: {PROJECT_FILE}"
        )


def main() -> None:
    validate_required_files()
    validate_project_identity()
    print("repo-integrity: ok")


if __name__ == "__main__":
    main()
