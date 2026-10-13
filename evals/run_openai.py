"""Run every fixture through an OpenAI model over the API.

`run_codex.py` measured `gpt-5.6-sol` through `codex exec`, which is the Codex
CLI: the model wrapped in an agent harness with its own preamble, its own
defaults, and possibly a different served build. `summarizer` would call the API
directly. Same model name, different arm — and the design spec is explicit that
Codex subscription credits cannot back a programmatic key, so the CLI path was
never shippable regardless of how well it scored.

This runner exists so `sol`'s 3/3 result on stance attribution can be checked
where it would actually run. Until that re-run happens, the run-006 and run-007
numbers describe a product that cannot be bought.

Kept symmetrical with `run_anthropic.py` and the Codex/Ollama arms:

- **No retries.** `max_retries=0`.
- **No structured outputs.** `text.format` would guarantee schema validity,
  which is the thing Gate 0a measures.
- **No reasoning-effort override.** Left at the API default, because picking one
  here would be tuning one arm and not the others.

Usage:
    python3 evals/run_openai.py --model gpt-5.6-sol --out evals/runs/run-008/sol-api
"""

import argparse
import sys
from pathlib import Path

import openai

from brief_contract import add_common_args, load_env_file, run_arm


def make_caller(client: openai.OpenAI, model: str, max_tokens: int):
    def call(system: str, user: str, timeout: float) -> tuple[str, str | None, dict | None]:
        try:
            response = client.responses.create(
                model=model,
                instructions=system,
                input=user,
                max_output_tokens=max_tokens,
                timeout=timeout,
            )
        except openai.APITimeoutError:
            return "", f"timeout after {timeout}s", None
        except openai.NotFoundError as exc:
            return "", f"unknown model {model!r}: {exc}", None
        except openai.RateLimitError as exc:
            return "", f"rate limited: {exc}", None
        except openai.APIStatusError as exc:
            return "", f"api {exc.status_code}: {str(exc)[:200]}", None
        except openai.APIConnectionError as exc:
            return "", f"connection error: {exc}", None

        usage = None
        if response.usage is not None:
            usage = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }

        # `incomplete` most often means the reasoning plus the Brief ran past
        # max_output_tokens. Reporting it as such beats reporting the truncated
        # remains as malformed JSON.
        if response.status == "incomplete":
            reason = getattr(response.incomplete_details, "reason", None)
            return response.output_text, f"incomplete response: {reason}", usage
        if response.status not in (None, "completed"):
            detail = getattr(response.error, "message", None)
            return response.output_text, f"status {response.status}: {detail}", usage

        return response.output_text, None, usage

    return call


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser, default_model="gpt-5.6-sol")
    args = parser.parse_args()

    load_env_file()
    try:
        client = openai.OpenAI(max_retries=0)
    except openai.OpenAIError as exc:
        print(f"could not construct client: {exc}", file=sys.stderr)
        print("set OPENAI_API_KEY in the environment or in .env", file=sys.stderr)
        return 2

    return run_arm(
        make_caller(client, args.model, args.max_tokens),
        model=args.model,
        arm=args.out.name,
        fixtures_dir=args.fixtures,
        out_dir=args.out,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    raise SystemExit(main())
