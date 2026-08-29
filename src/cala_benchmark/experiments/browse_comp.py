"""Thin wrappers around the canonical Inspect Evals BrowseComp task.

BrowseComp owns the dataset and scorer; Inspect AI owns evaluation, agent
orchestration, logging, and token accounting. This module only supplies the
experiment-specific retrieval configuration.

The Cala arm uses Cala's hosted MCP server. MCP is the transport/interface
layer; the model still sees ordinary callable tools and produces normal tool
calls. We therefore treat MCP vs native/local tools as an implementation detail,
not as the experimental variable.
"""

import os

from inspect_ai import Task
from inspect_ai.agent import react, run
from inspect_ai.solver import Solver
from inspect_ai.tool import mcp_server_http, mcp_tools, web_browser, web_search
from inspect_evals.browse_comp import browse_comp
from inspect_evals.browse_comp.prompts import QUERY_TEMPLATE


RESEARCH_PROMPT = (
    "You are an expert web research assistant. Research the question carefully, "
    "using the available external knowledge tools as needed. Cross-check important "
    "facts and answer only after sufficient research."
)


def web_solver() -> Solver:
    """Web baseline using Inspect's standard web search/browser tools."""
    agent = react(
        name="web_researcher",
        description="Web research assistant using generic web retrieval",
        prompt=RESEARCH_PROMPT,
        tools=[web_search(), *web_browser()],
    )

    async def solve(state, generate):
        result = await run(agent, QUERY_TEMPLATE.format(Question=state.input_text))
        state.output.completion = result.output.completion
        return state

    return solve


def cala_server():
    """Create the hosted Cala MCP server connection.

    Cala documents https://api.cala.ai/mcp/ as its MCP endpoint and X-API-KEY
    as the authentication header. The key is read at runtime so it is never
    committed to the repository.
    """
    api_key = os.environ.get("CALA_API_KEY")
    if not api_key:
        raise RuntimeError("CALA_API_KEY must be set to run the Cala experiment")

    return mcp_server_http(
        name="Cala",
        url="https://api.cala.ai/mcp/",
        headers={"X-API-KEY": api_key},
        execution="local",
    )


def cala_solver() -> Solver:
    """Cala arm using Cala's MCP tools through Inspect."""
    cala = cala_server()
    cala_tool_source = mcp_tools(
        cala,
        tools=[
            "knowledge_search",
            "knowledge_query",
            "entity_search",
            "retrieve_entity",
        ],
    )

    agent = react(
        name="cala_researcher",
        description="Web research assistant using Cala knowledge retrieval",
        prompt=RESEARCH_PROMPT,
        tools=[cala_tool_source],
    )

    async def solve(state, generate):
        result = await run(agent, QUERY_TEMPLATE.format(Question=state.input_text))
        state.output.completion = result.output.completion
        return state

    return solve


def web_task(num_samples: int | None = None) -> Task:
    """Canonical BrowseComp dataset/scorer with the web baseline solver."""
    return browse_comp(num_samples=num_samples, solver=web_solver())


def cala_task(num_samples: int | None = None) -> Task:
    """Canonical BrowseComp dataset/scorer with the Cala MCP solver."""
    return browse_comp(num_samples=num_samples, solver=cala_solver())
