# Lateralus Story Finder

Lateralus Story Finder is being developed through small, governed vertical slices.

Product behavior will be documented in a public specification before implementation begins.

## Project identity

The repository identity is committed in [`.lateralus/project.json`](.lateralus/project.json).
Harness operations must treat a missing or malformed identity file as a hard error; they must
not infer identity from a checkout path, repository basename, or another project's defaults.

Run the deterministic repository integrity check locally with:

```sh
python3 scripts/check_repo_integrity.py
```
