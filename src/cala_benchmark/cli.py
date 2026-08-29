"""Run a BrowseComp experiment arm through Inspect AI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from collections import Counter

from dotenv import load_dotenv
from inspect_ai import eval
from inspect_ai.log import EvalLog

from cala_benchmark.experiments.browse_comp import cala_task, web_task

DEFAULT_LOG_DIR = Path.cwd() / "results"
DEFAULT_MODEL = "openai/gpt-4o-mini"


def _load_env() -> None:
    load_dotenv(Path.cwd() / ".env")
    load_dotenv()


def _retrieval_counts(log: EvalLog) -> dict[str, int]:
    """Count Inspect function tools and OpenAI-native web_search calls.

    OpenAI's built-in search is a Responses API tool (`type: web_search`).
    It does not appear as an Inspect `ToolEvent`, so function-tool counts
    alone make the web arm look like it never retrieved.
    """
    function_tools: Counter[str] = Counter()
    native_web_search = 0
    for sample in log.samples or []:
        for ev in sample.events or []:
            event = getattr(ev, "event", None) or type(ev).__name__
            if event in ("tool", "ToolEvent") or type(ev).__name__ == "ToolEvent":
                name = getattr(ev, "function", None) or "unknown"
                if name != "submit":
                    function_tools[name] += 1
            if event in ("model", "ModelEvent") or type(ev).__name__ == "ModelEvent":
                call = getattr(ev, "call", None)
                resp = getattr(call, "response", None) if call is not None else None
                if isinstance(resp, dict):
                    usage = resp.get("tool_usage") or {}
                    search = usage.get("web_search") or {}
                    native_web_search += int(search.get("num_requests") or 0)
    return {
        "function_tool_calls": sum(function_tools.values()),
        "native_web_search_requests": native_web_search,
        **{f"function:{name}": count for name, count in sorted(function_tools.items())},
    }


def _print_log_summary(log: EvalLog) -> None:
    """Print run metadata only — never sample questions or answers."""
    print(f"status: {log.status}")
    print(f"log: {log.location}")
    if log.eval is not None:
        print(f"model: {log.eval.model}")
        print(f"task: {log.eval.task}")
        if log.eval.metadata:
            print(f"variant: {log.eval.metadata.get('variant')}")
    if log.stats is not None:
        print(f"started: {log.stats.started_at}")
        print(f"completed: {log.stats.completed_at}")
        for model_name, usage in log.stats.model_usage.items():
            print(
                f"usage[{model_name}]: "
                f"input={usage.input_tokens} "
                f"cache_read={usage.input_tokens_cache_read} "
                f"cache_write={usage.input_tokens_cache_write} "
                f"output={usage.output_tokens} "
                f"total={usage.total_tokens} "
                f"cost={usage.total_cost}"
            )
    if log.results is not None:
        for score in log.results.scores:
            metrics = {
                name: (metric.value if hasattr(metric, "value") else metric)
                for name, metric in score.metrics.items()
            }
            print(f"score[{score.name}]: {metrics}")
    n_samples = len(log.samples or [])
    print(f"samples_logged: {n_samples}")
    retrieval = _retrieval_counts(log)
    print(
        "retrieval: "
        f"function_tools={retrieval['function_tool_calls']} "
        f"native_web_search={retrieval['native_web_search_requests']}"
    )
    for key, value in retrieval.items():
        if key.startswith("function:"):
            print(f"  {key}: {value}")


def _require_model_credentials(model: str) -> None:
    provider = model.split("/", 1)[0]
    required = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
    }
    env_name = required.get(provider)
    if env_name and not os.environ.get(env_name):
        raise SystemExit(f"{env_name} must be set to run model {model}.")


def main() -> None:
    _load_env()

    parser = argparse.ArgumentParser(
        description=(
            "Run the Cala context-efficiency experiment. "
            "Both arms use the same BrowseComp samples, model, and ReAct agent; "
            "only retrieval tools differ."
        )
    )
    parser.add_argument("variant", choices=["web", "cala"])
    parser.add_argument(
        "--samples",
        type=int,
        default=2,
        help="First N BrowseComp samples (deterministic; same N pairs the arms).",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("INSPECT_EVAL_MODEL", DEFAULT_MODEL),
        help="Inspect model id. Must be identical across arms.",
    )
    parser.add_argument(
        "--log-dir",
        default=str(DEFAULT_LOG_DIR),
        help="Inspect log directory (gitignored). Contains benchmark text; keep local.",
    )
    parser.add_argument(
        "--message-limit",
        type=int,
        default=40,
        help="Max messages per sample (same for both arms).",
    )
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument(
        "--sample-id",
        nargs="+",
        default=None,
        help="Optional explicit BrowseComp sample ids for paired runs.",
    )
    args = parser.parse_args()

    _require_model_credentials(args.model)
    if args.variant == "cala" and not os.environ.get("CALA_API_KEY"):
        raise SystemExit("CALA_API_KEY must be set to run the Cala arm.")

    if args.variant == "web":
        task = web_task(args.samples, scorer_model=args.model)
    else:
        task = cala_task(args.samples, scorer_model=args.model)

    eval_kwargs: dict = {
        "model": args.model,
        "log_dir": args.log_dir,
        "metadata": {
            "experiment": "cala-context-efficiency",
            "variant": args.variant,
            "benchmark": "browse_comp",
        },
        "tags": ["cala-context-efficiency", args.variant],
        "sample_shuffle": False,
        "message_limit": args.message_limit,
        "continue_on_fail": True,
    }
    if args.sample_id:
        eval_kwargs["sample_id"] = args.sample_id
    if args.temperature is not None:
        eval_kwargs["temperature"] = args.temperature
    if args.max_tokens is not None:
        eval_kwargs["max_tokens"] = args.max_tokens

    logs = eval(task, **eval_kwargs)
    for log in logs:
        _print_log_summary(log)


if __name__ == "__main__":
    main()
