# Cala Context Efficiency Benchmark

An experiment measuring whether Cala's knowledge/context layer can reduce the context and LLM cost required by a research agent.

This repository is **not** a new evaluation framework. It is a thin orchestration layer over Inspect AI and Inspect Evals.

## Framework choice

- **Evaluation framework:** [Inspect AI](https://inspect.aisi.org.uk/)
- **Benchmark collection:** [Inspect Evals](https://github.com/UKGovernmentBEIS/inspect_evals)
- **Initial benchmark:** BrowseComp (1,266 samples)
- **Canonical benchmark implementation/scorer:** `inspect_evals.browse_comp`

Inspect provides agent/tool orchestration, execution, logging, token usage, and evaluation infrastructure. Inspect Evals provides the BrowseComp dataset adapter and scorer. This repo only supplies the experiment-specific retrieval configuration.

## Experiment

Run the same research-agent setup against the **same** BrowseComp tasks with two context mechanisms:

1. **Web baseline** — Inspect's generic `web_search` / `web_browser` tools (the BrowseComp browsing setup).
2. **Cala** — Cala's hosted MCP server, exposing Cala knowledge tools to the same Inspect ReAct agent.

The model, task prompt, generation settings, and execution limits stay constant. The retrieval/context layer is the experimental variable.

```text
Same benchmark
Same agent
Same model
Same prompt
Same generation settings
Same execution limits
        │
        ├───────────────┐
        │               │
   Web retrieval     Cala MCP
        │               │
        └───────┬───────┘
                │
             Same LLM
                │
         BrowseComp scorer
                │
          Inspect logs
```

### Primary question

> Can a context/knowledge layer reduce the cost of completing the same research task while maintaining comparable task performance?

### Primary metric

**Cost per successful task.**

Supporting metrics come from Inspect logs:

- BrowseComp accuracy (`browse_comp_accuracy`)
- input / cached input / output / total tokens
- estimated model cost (`ModelUsage.total_cost`)
- model calls / turns
- tool calls and tool latency (transcript `ToolEvent`s)
- sample `total_time`

Do not duplicate Inspect's token accounting.

## Why MCP?

Cala's hosted MCP endpoint is `https://api.cala.ai/mcp/`, authenticated with `X-API-KEY`. Inspect supports HTTP MCP servers directly (`mcp_server_http`), so this experiment does not include a Cala REST client.

MCP is **not** the experimental variable. Inspect exposes MCP capabilities as ordinary tools: the model still receives tool definitions, emits tool calls, and receives tool results. Local MCP execution (`execution="local"`) means Inspect performs the HTTP round trip, so tool results land in Inspect logs the same way web-tool results do.

Measure both:

- **LLM context efficiency:** input tokens, cached tokens, output tokens, total cost.
- **Tool/transport efficiency:** number of calls, tool latency, end-to-end latency.

The Cala arm is filtered to the research tools actually advertised by `https://api.cala.ai/mcp/`:

- `knowledge_search`
- `knowledge_query`
- `entity_search`
- `entity_retrieval`

`entity_introspection` is omitted so the Cala tool catalog is not larger than it needs to be. Tool definitions themselves consume context. The server currently exposes five tools; we keep four.

The Cala arm has **no web/browser fallback**. That would turn the comparison into web vs web+Cala.

## Why BrowseComp?

BrowseComp is designed for difficult browsing-agent questions that generally require web access and multi-hop research. Inspect Evals ships the adapter and canonical scorer.

Do not copy BrowseComp questions or answers into this repository, the README, tests, or committed logs. The BrowseComp authors ask that examples not be reproduced online.

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
```

The shared solver factory is `create_solver(tools)` in `src/cala_benchmark/experiments/browse_comp.py`. Both arms wrap that factory; only the tool list changes.

The shared research prompt requires retrieval before submit. That instruction is identical on both arms.

OpenAI `web_search` is a native Responses API tool (`type: web_search`), not an Inspect function call. It will not show up as a `ToolEvent`. Count `response.tool_usage.web_search.num_requests` / `web_search_call` items when comparing retrieval volume. The runner prints both function-tool calls and native web-search requests so the web arm is not mistaken for “no retrieval.”

## Install

Python 3.11–3.13.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Validated against `inspect-ai==0.3.260`, `inspect-evals==0.18.0`, and `mcp==2.1.1`.

Fill in `.env`. Never commit the real file.

The **web** arm uses Inspect's `web_browser` tool, which needs Docker and the BrowseComp compose image (`aisiuk/inspect-tool-support`). The **Cala** arm does not use a sandbox.

OpenAI models such as `openai/gpt-4o-mini` can use Inspect's built-in OpenAI web search. If you run a non-OpenAI model, set `TAVILY_API_KEY` or Google CSE credentials as a `web_search` fallback.

## Smoke test

Use a small paired subset. Do not treat these numbers as the experiment result.

Both commands must use the same `--samples` count and `--model`. Samples are the first N BrowseComp rows with `sample_shuffle=false`, so the task IDs match across arms.

Web (requires Docker):

```bash
python scripts/run.py web --samples 2 --model openai/gpt-4o-mini
```

Cala (requires `CALA_API_KEY`):

```bash
export CALA_API_KEY=...
python scripts/run.py cala --samples 2 --model openai/gpt-4o-mini
```

Equivalent Inspect CLI:

```bash
inspect eval src/cala_benchmark/experiments/browse_comp.py@browse_comp_web \
  --model openai/gpt-4o-mini -T num_samples=2 --sample-shuffle false

inspect eval src/cala_benchmark/experiments/browse_comp.py@browse_comp_cala \
  --model openai/gpt-4o-mini -T num_samples=2 --sample-shuffle false
```

Logs are written to `results/` (gitignored). Inspect logs include decrypted BrowseComp text — keep them local.

View logs:

```bash
inspect view
```

Useful runner flags (applied identically if you pass them on both arms):

```text
--samples N          first N BrowseComp samples (default 2)
--model MODEL        Inspect model id
--log-dir DIR        Inspect log directory (default ./results)
--message-limit N    max messages per sample (default 40)
--temperature T      generation temperature
--max-tokens N       max output tokens
--sample-id ID ...   explicit paired sample ids
```

## Environment variables

| Variable | Used by |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI models and OpenAI built-in web search |
| `INSPECT_EVAL_MODEL` | default `--model` if the flag is omitted |
| `CALA_API_KEY` | Cala MCP `X-API-KEY` header |
| `TAVILY_API_KEY` | optional `web_search` fallback |
| `GOOGLE_CSE_ID` / `GOOGLE_CSE_API_KEY` | optional Google `web_search` fallback |

Do not put keys in YAML.

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

## What Inspect logs contain

Each run writes a native Inspect `.eval` log. Useful fields for later aggregation (not implemented here yet):

| Need | Where in the log |
| --- | --- |
| task / sample id | `EvalSample.id` (stable `browse_comp-...` ids) |
| variant | `eval.metadata.variant` |
| model | `eval.model` |
| success | BrowseComp score `value["score"]` (`C` / `I`) |
| input tokens | `ModelUsage.input_tokens` |
| cached input tokens | `ModelUsage.input_tokens_cache_read` |
| output tokens | `ModelUsage.output_tokens` |
| total tokens | `ModelUsage.total_tokens` |
| estimated model cost | `ModelUsage.total_cost` |
| sample latency | `EvalSample.total_time` |
| tool calls / tool latency | transcript `ToolEvent`s; OpenAI native search via `tool_usage.web_search` |
| model calls | assistant messages / model events |

Read logs with `inspect_ai.log.read_eval_log` or `inspect view`. Do not commit them.

## Results

Aggregate reporting comes after a real paired run. This README will not contain placeholder numbers.

The interesting outcome is not necessarily higher Cala accuracy. Comparable accuracy at lower input tokens / cost per success would support the hypothesis.

Do not draw conclusions from a 2–10 sample smoke test.

## Status

The web and Cala arms are wired through Inspect AI / Inspect Evals BrowseComp with a shared ReAct solver. Next: a 2-sample smoke test to confirm BrowseComp loads, both tool surfaces execute, the scorer runs, and Inspect usage logs are written. Then scale the paired sample set. Do not run all 1,266 tasks until that path is verified.
