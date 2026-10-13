"""Run every fixture through a Claude model over the Anthropic API.

The arm this eval has recommended since run-004 has never been measured this
way. Sonnet's numbers came from subagents on a Claude Code subscription that
read files and wrote the JSON themselves — the records still carry
`seconds: None, raw: None` because no runner produced them. The Owner cannot
power this project from that subscription; `summarizer` will call the API, once,
and take what it gets.

So this file is not a new arm. It is the missing half of the harness: the first
time the incumbent gets measured on the path it would actually ship on.

Deliberately absent, because the Codex and Ollama arms do not have them:

- **No retries.** `max_retries=0`. The SDK's default of 2 would silently give
  this arm attempts the others never had.
- **No structured outputs.** `output_config.format` would guarantee a valid
  Brief, which is precisely what Gate 0a is trying to measure.
- **No revision loop.** One call, parse, record.

Also absent by necessity: `temperature`. Sampling parameters were removed on
Sonnet 5 and Opus 5 and return a 400.

Usage:
    python3 evals/run_anthropic.py --model claude-sonnet-5 --out evals/runs/run-008/sonnet-api
"""

import argparse
import sys
from pathlib import Path

import anthropic

from brief_contract import add_common_args, load_env_file, run_arm


def make_caller(client: anthropic.Anthropic, model: str, max_tokens: int):
    def call(system: str, user: str, timeout: float) -> tuple[str, str | None, dict | None]:
        try:
            message = client.with_options(timeout=timeout).messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.APITimeoutError:
            return "", f"timeout after {timeout}s", None
        except anthropic.NotFoundError as exc:
            return "", f"unknown model {model!r}: {exc}", None
        except anthropic.RateLimitError as exc:
            return "", f"rate limited: {exc}", None
        except anthropic.APIStatusError as exc:
            return "", f"api {exc.status_code}: {str(exc)[:200]}", None
        except anthropic.APIConnectionError as exc:
            return "", f"connection error: {exc}", None

        usage = {
            "input_tokens": message.usage.input_tokens,
            "output_tokens": message.usage.output_tokens,
        }

        # A refusal is a real production outcome, not a crash. Record it as the
        # failure it is rather than letting it read as malformed JSON.
        if message.stop_reason == "refusal":
            detail = getattr(message.stop_details, "category", None)
            return "", f"refused by safety classifier (category: {detail})", usage
        if message.stop_reason == "max_tokens":
            return "", f"hit max_tokens ceiling of {max_tokens}", usage

        text = "".join(block.text for block in message.content if block.type == "text")
        return text, None, usage

    return call


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_args(parser, default_model="claude-sonnet-5")
    args = parser.parse_args()

    load_env_file()
    try:
        client = anthropic.Anthropic(max_retries=0)
    except anthropic.AnthropicError as exc:
        print(f"could not construct client: {exc}", file=sys.stderr)
        print("set ANTHROPIC_API_KEY in the environment or in .env", file=sys.stderr)
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
