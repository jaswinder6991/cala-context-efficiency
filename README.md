# Cala Context Efficiency Benchmark

A small experiment measuring whether a knowledge/context layer can reduce the context and LLM cost required by a research agent.

## Experiment

We run the **same agent and model** on an existing research-agent benchmark with two retrieval configurations:

1. **Web baseline** — generic web search/retrieval.
2. **Cala** — Cala knowledge retrieval.

The project intentionally does **not** implement its own benchmark dataset or evaluator. The benchmark and canonical evaluation remain external dependencies; this repository orchestrates runs, captures traces, and reports results.

### Primary question

> Can a context/knowledge layer reduce the cost of completing the same research task while maintaining comparable task performance?

### Primary metric

**Cost per successful task**.

Secondary metrics:

- task accuracy / score from the canonical evaluator
- LLM input tokens
- total LLM tokens
- LLM calls
- retrieval calls
- retrieved/context tokens where measurable
- latency
- estimated LLM cost

## Initial benchmark

**BrowseComp** is the intended first benchmark because it focuses on difficult, multi-hop web research and therefore exercises the context-acquisition problem we want to measure.

The benchmark's canonical tasks/evaluator are not copied into this repository.

## Design principles

- Same benchmark tasks
- Same model
- Same agent loop
- Same prompts and generation settings where possible
- Same execution limits
- Only the retrieval/context mechanism changes
- Use the benchmark's existing evaluator rather than inventing a judge
- Keep raw traces separate from summarized results
- Make every experimental assumption explicit

## Repository layout

```text
src/cala_benchmark/
├── agents/             # Retrieval adapters / agent configuration
├── benchmarks/         # Thin adapters around external benchmarks
├── instrumentation/    # Token, cost, latency and trace collection
├── runner.py           # Experiment orchestration
└── reporting.py        # Aggregate comparison output

configs/                # Reproducible experiment configurations
scripts/                # CLI entry points
results/                # Local experiment outputs; raw data is gitignored
```

## Status

Scaffold only. The next step is to wire the canonical BrowseComp evaluation and implement the two retrieval configurations without changing the benchmark itself.
