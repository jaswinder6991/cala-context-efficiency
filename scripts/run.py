"""Run a BrowseComp experiment through Inspect AI."""

import argparse

from inspect_ai import eval

from cala_benchmark.experiments.browse_comp import cala_task, web_task


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=["web", "cala"])
    parser.add_argument("--samples", type=int, default=10)
    parser.add_argument("--model", default="openai/gpt-5-mini")
    args = parser.parse_args()

    task = web_task(args.samples) if args.variant == "web" else cala_task(args.samples)
    eval(task, model=args.model)


if __name__ == "__main__":
    main()
