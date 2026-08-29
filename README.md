# Cala Context Efficiency Benchmark

An experiment measuring whether Cala's knowledge/context layer can reduce the context and LLM cost required by a research agent.

## Framework choice

This project intentionally does **not** implement its own evaluation framework or benchmark.

- **Evaluation framework:** [Inspect AI](https://inspect.aisi.org.uk/)
- **Benchmark collection:** [Inspect Evals](https://github.com/UKGovernmentBEIS/inspect_evals)
- **Initial benchmark:** BrowseComp (1,266 samples)
- **Canonical benchmark implementation/scorer:** `inspect_evals.browse_comp`

Inspect provides agent/tool orchestration, execution, logging, token usage and evaluation infrastructure. Inspect Evals provides the BrowseComp dataset adapter and scorer. Our code should only supply the experiment-specific retrieval configuration.

## Experiment

Run the same research-agent setup against the same BrowseComp tasks with two context mechanisms:

1. **Web baseline** — Inspect's generic web search/browser tools.
2. **Cala** — Cala's hosted MCP server, exposing Cala knowledge tools to the same Inspect ReAct agent.

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

## Why MCP?

Cala provides a hosted MCP endpoint at `https://api.cala.ai/mcp/`. Inspect supports HTTP MCP servers directly, so there is no need to write a Cala API client or custom tool adapter.

MCP is **not** intended to be the experimental variable. At the model layer, MCP exposes ordinary callable tools: the model still receives tool definitions, emits tool calls, and receives tool results. Inspect's MCP integration handles the protocol/transport underneath. Inspect can execute HTTP MCP locally, which is what this experiment uses.

There is still transport overhead to measure: Cala calls involve an HTTP/MCP round trip, while Inspect's built-in web tools have their own implementation path. That overhead should appear in latency and tool timing, but it should not be confused with LLM context-token cost. We therefore report both **LLM token/cost metrics** and **wall-clock/tool latency**.

We also explicitly filter the Cala MCP surface to four research tools:

- `knowledge_search`
- `knowledge_query`
- `entity_search`
- `retrieve_entity`

This avoids giving the model an unnecessarily large MCP tool catalog. Inspect supports tool selection for MCP servers, and tool definitions themselves consume model context, so tool-surface size is an experimental control rather than an incidental detail.

### Why not use Cala's API directly?

We could call `/v1/knowledge/search` and `/v1/knowledge/query` ourselves, but doing that would create custom plumbing and move the experiment away from the way agents naturally consume Cala. MCP lets us test Cala in the same external-tool interaction pattern as the web baseline while keeping our code thin.

## Tool calling vs MCP

A useful distinction:

```text
LLM
 │
 │ normal tool call
 ▼
Inspect tool interface
 │
 ├── Web tool implementation
 │
 └── MCP tool source
       │
       ▼
   Cala MCP server
```

MCP does not inherently require a different kind of LLM reasoning. It standardizes how tools are discovered and invoked. The protocol can add serialization/network overhead, but that is separate from the model's input/output token accounting.

For this reason, we should **not** make a native Python Cala wrapper for the benchmark. The Cala arm should use MCP, and the README/results should explicitly distinguish:

- **LLM context efficiency:** input tokens, cached tokens, output tokens, total cost.
- **Tool/transport efficiency:** number of calls, tool latency, end-to-end latency.

If we later want to measure pure transport overhead, that should be a separate microbenchmark rather than contaminating the main context-efficiency result.

## Why BrowseComp?

BrowseComp is designed for difficult browsing-agent questions that generally require web access and multi-hop research. Inspect Evals ships the benchmark adapter and canonical scorer.

The benchmark contains 1,266 samples. We can start with a small reproducible subset for development and then run the full benchmark when the experiment is stable.

## Architecture

```text
                 Inspect Evals
                 BrowseComp
                     │
                     ▼
                 Inspect AI
                ReAct agent
                     │
             ┌───────┴────────┐
             │                │
      Web tools          Cala MCP tools
      search/browser     search/query/entities
             │                │
             └───────┬────────┘
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
└── experiments/
    └── browse_comp.py     # Thin Inspect task + retrieval configuration

configs/                   # Reproducible experiment settings
scripts/run.py             # Run web or Cala arm
results/                   # Local Inspect logs/results; gitignored
```

## Running

Install the project and set the model provider credentials required by Inspect.

Web baseline:

```bash
python scripts/run.py web --samples 10 --model openai/gpt-5-mini
```

Cala:

```bash
export CALA_API_KEY=...
python scripts/run.py cala --samples 10 --model openai/gpt-5-mini
```

The first development run should use a small sample count. Do not interpret small-sample results as the final benchmark result.

## Experimental constraints

1. Same BrowseComp samples for both arms.
2. Same model and generation settings.
3. Same agent scaffold and research prompt.
4. Same execution limits.
5. Only retrieval/context tools differ.
6. Use the canonical BrowseComp scorer.
7. Do not copy the benchmark dataset into this repository.
8. Do not introduce a custom LLM judge unless the canonical evaluation requires it.
9. Keep MCP transport overhead separate from LLM context-cost analysis.
10. Report enough per-sample data to make failures and cost differences inspectable.

The goal is to compare **context mechanisms**, not to create another benchmark.

## Status

The repository now has both experiment arms wired through Inspect AI. The Cala arm uses Cala's hosted MCP endpoint rather than a custom API adapter. Next step is a small end-to-end run to validate the BrowseComp scorer, MCP connection, tool names, and Inspect usage logs before scaling the experiment.
