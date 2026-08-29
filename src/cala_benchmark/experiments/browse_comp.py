"""Thin wrappers around the canonical Inspect Evals BrowseComp task.

BrowseComp owns the dataset and scorer; Inspect AI owns evaluation, agent
orchestration, logging, and token accounting. This module only supplies the
experiment-specific retrieval configuration.

Both arms share one ReAct solver factory. The experimental variable is the
retrieval tool surface, not the agent, prompt, model, or MCP-vs-tool-calling.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Final

from inspect_ai import Task, task
from inspect_ai.agent import react, run
from inspect_ai.solver import Generate, Solver, TaskState, solver
from inspect_ai.tool import (
    Tool,
    ToolDef,
    ToolSource,
    mcp_server_http,
    mcp_tools,
    web_browser,
    web_search,
)
from inspect_evals.browse_comp import browse_comp
from inspect_evals.browse_comp.prompts import QUERY_TEMPLATE

ToolLike = Tool | ToolDef | ToolSource

CALA_MCP_URL: Final = "https://api.cala.ai/mcp/"

# Shared across arms. Do not mention web search, browsing, or Cala by name —
# that would become a prompt difference rather than a tool difference.
# Require tool use on both arms so the web baseline cannot skip retrieval
# and answer from parametric memory.
RESEARCH_PROMPT: Final = """
You are an expert research assistant. You must use the available external
knowledge tools to research the question before answering. Do not answer from
memory or prior knowledge alone — look the information up. Cross-check
important facts with a follow-up tool call when needed. Submit only after
you have used at least one retrieval tool. Note that all the questions have
a valid answer, but will likely require looking up information.
""".strip()

# Confirmed against https://api.cala.ai/mcp/ on 2026-08-29.
# entity_introspection is intentionally omitted.
# retrieve_entity is kept as an alias in case the server name changes.
CALA_TOOL_NAMES: Final = [
    "knowledge_search",
    "knowledge_query",
    "entity_search",
    "entity_retrieval",
    "retrieve_entity",
]

# Match Inspect Evals' BrowseComp browsing_solver search-provider order.
WEB_SEARCH_PROVIDERS: Final = [
    "openai",
    "tavily",
    {"google": {"model": "openai/gpt-4o-mini"}},
]


def create_solver(tools: Sequence[ToolLike]) -> Solver:
    """Identical ReAct agent for every arm; only `tools` varies."""

    @solver
    def research_solver() -> Solver:
        agent = react(
            name="researcher",
            description="Research assistant",
            prompt=RESEARCH_PROMPT,
            tools=list(tools),
        )

        async def solve(state: TaskState, generate: Generate) -> TaskState:
            agent_state = await run(
                agent,
                QUERY_TEMPLATE.format(Question=state.input_text),
            )
            state.output = agent_state.output
            if agent_state.messages:
                state.messages = agent_state.messages
            return state

        return solve

    return research_solver()


def web_tools() -> list[ToolLike]:
    """Inspect web search + browser, matching BrowseComp's browsing setup.

    `web_search` is the primary retrieval path. `web_browser` requires Inspect's
    Docker sandbox (the BrowseComp default compose image).
    """
    return [
        web_search(providers=WEB_SEARCH_PROVIDERS),
        *web_browser(),
    ]


def cala_server():
    """Hosted Cala MCP server. Auth is read at runtime and never committed."""
    api_key = os.environ.get("CALA_API_KEY")
    if not api_key:
        raise RuntimeError("CALA_API_KEY must be set to run the Cala experiment")

    return mcp_server_http(
        name="Cala",
        url=CALA_MCP_URL,
        headers={"X-API-KEY": api_key},
        execution="local",
        timeout=120,
        sse_read_timeout=300,
    )


def cala_tools() -> list[ToolLike]:
    """Cala knowledge tools via Inspect MCP. No browser fallback."""
    return [
        mcp_tools(cala_server(), tools=CALA_TOOL_NAMES),
    ]


def web_solver() -> Solver:
    return create_solver(web_tools())


def cala_solver() -> Solver:
    return create_solver(cala_tools())


def web_task(
    num_samples: int | None = None,
    scorer_model: str | None = None,
) -> Task:
    """Canonical BrowseComp dataset/scorer with the web retrieval solver."""
    return browse_comp(
        num_samples=num_samples,
        solver=web_solver(),
        scorer_model=scorer_model,
    )


def cala_task(
    num_samples: int | None = None,
    scorer_model: str | None = None,
) -> Task:
    """Canonical BrowseComp dataset/scorer with the Cala MCP solver.

    Sandbox is disabled: Cala tools are remote HTTP MCP, not Playwright.
    """
    return browse_comp(
        num_samples=num_samples,
        solver=cala_solver(),
        scorer_model=scorer_model,
        sandbox=None,
    )


@task
def browse_comp_web(num_samples: int = 2, scorer_model: str | None = None) -> Task:
    """Inspect CLI entry: web retrieval arm."""
    return web_task(num_samples, scorer_model=scorer_model)


@task
def browse_comp_cala(num_samples: int = 2, scorer_model: str | None = None) -> Task:
    """Inspect CLI entry: Cala MCP arm."""
    return cala_task(num_samples, scorer_model=scorer_model)
