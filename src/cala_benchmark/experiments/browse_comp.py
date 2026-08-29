"""Thin wrappers around the canonical Inspect Evals BrowseComp task.

BrowseComp owns the dataset and scorer; Inspect AI owns evaluation, agent
orchestration, logging, and token accounting. This module only supplies the
experiment-specific retrieval configuration.
"""

from inspect_ai import Task
from inspect_ai.agent import react, run
from inspect_ai.solver import Solver
from inspect_ai.tool import web_browser, web_search
from inspect_evals.browse_comp import browse_comp
from inspect_evals.browse_comp.prompts import QUERY_TEMPLATE


def web_solver() -> Solver:
    """Web baseline using Inspect's standard web search/browser tools."""
    agent = react(
        name="web_researcher",
        description="Web research assistant",
        prompt=(
            "You are an expert web research assistant. Use web_search to find relevant "
            "information and web_browser to inspect pages. Answer the BrowseComp question "
            "carefully and only after sufficient research."
        ),
        tools=[web_search(), *web_browser()],
    )

    async def solve(state, generate):
        result = await run(agent, QUERY_TEMPLATE.format(Question=state.input_text))
        state.output.completion = result.output.completion
        return state

    return solve


def web_task(num_samples: int | None = None) -> Task:
    """Canonical BrowseComp dataset/scorer with the web baseline solver."""
    return browse_comp(num_samples=num_samples, solver=web_solver())


# Cala will be added here once its API/MCP integration is verified. The Cala
# variant must reuse this exact BrowseComp task/scorer and differ only in
# retrieval tools.
