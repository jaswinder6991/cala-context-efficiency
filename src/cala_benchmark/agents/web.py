from .base import AgentResult, ResearchAgent


class WebAgent(ResearchAgent):
    """Baseline agent using generic web retrieval.

    The concrete LLM/search implementation will be added after the
    benchmark contract is finalized.
    """

    def run(self, task: str) -> AgentResult:
        raise NotImplementedError
