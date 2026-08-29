"""Run the current experiment through Inspect AI."""

from inspect_ai import eval

from cala_benchmark.experiments.browse_comp import web_task


if __name__ == "__main__":
    eval(web_task(num_samples=10), model="openai/gpt-5-mini")
