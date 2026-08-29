from .base import AgentResult, ResearchAgent


class CalaAgent(ResearchAgent):
    """Agent using Cala as its knowledge/context retrieval layer."""

    def run(self, task: str) -> AgentResult:
        raise NotImplementedError
