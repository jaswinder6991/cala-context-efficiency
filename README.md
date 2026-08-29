# Cala Context Efficiency Benchmark

An experiment measuring whether Cala's knowledge/context layer can reduce the context and LLM cost required by a research agent.

## Framework choice

This project intentionally does **not** implement its own evaluation framework or benchmark.

- **Evaluation framework:** [Inspect AI](https://inspect.aisi.org.uk/)
- **Benchmark collection:** [Inspect Evals](https://github.com/UKGovernmentBEIS/inspect_evals)
- **Initial benchmark:** BrowseComp (1,266 samples)
- **Canonical benchmark implementation/scorer:** `inspect_evals.browse_comp`

Inspect provides the agent/tool orchestration, execution, logging, token usage and evaluation infrastructure. Inspect Evals provides the BrowseComp dataset adapter and scorer. Our code should only supply the experiment-specific retrieval configuration and result comparison.

## Experiment

Run the same research-agent setup against the same BrowseComp tasks with two context mechanisms:

1. **Web baseline** — generic web search/browser tools.
2. **Cala** — Cala knowledge retrieval tools.

The model, task prompt, generation settings and execution limits should remain constant. The retrieval/context layer is the experimental variable.

### Primary question

> Can a context/knowledge layer reduce the cost of completing the same research task while maintaining comparable task performance?

### Primary metric

**Cost per successful task.**

Supporting metrics should come from Inspect's logs where available:

- BrowseComp accuracy
- input/output/total token usage
- model calls / turns
- tool calls
- latency
- estimated model cost

We should not duplicate Inspect's token accounting or logging implementation.

## Why BrowseComp?

BrowseComp is specifically designed for difficult browsing-agent questions that generally require web access and multi-hop research. Inspect Evals already ships a maintained BrowseComp implementation, including the dataset download/checksum and canonical scorer.

The benchmark contains 1,266 samples. We can start with a small reproducible subset for development and then run the full benchmark when the experiment is stable.

## Architecture

```text
                 Inspect Evals
                 BrowseComp
                     │
                     ▼
                 Inspect AI
               evaluation runner
                     │
             ┌───────┴───────┐
             │               │
        Web context     Cala context
             │               │
             └───────┬───────┘
                     │
                  same LLM
                     │
                     ▼
             Inspect scorer/logs
                     │
                     ▼
              comparison report
```

## Repository layout

```text
src/cala_benchmark/
├── experiments/       # Thin Inspect task wrappers / retrieval configuration
├── tools/             # Cala-specific tool adapter(s)
└── reporting/         # Experiment comparison only; no scoring logic

configs/               # Reproducible experiment settings
scripts/               # Small CLI entry points
results/               # Local Inspect logs/results; gitignored
```

## Important experimental constraint

We should avoid changing the BrowseComp task or its scorer. In particular, do not copy the benchmark dataset into this repository and do not introduce a custom LLM judge unless the canonical evaluation requires it.

The goal is to compare **context mechanisms**, not to create another benchmark.

## Status

Scaffold updated to use Inspect AI + Inspect Evals. Next step: implement the two retrieval configurations as Inspect tools/solvers and verify that both can run through the existing BrowseComp task without changing its scorer.
