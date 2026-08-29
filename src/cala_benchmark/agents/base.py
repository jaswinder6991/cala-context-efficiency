from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    answer: str
    trace: list[dict[str, Any]] = field(default_factory=list)


class ResearchAgent(ABC):
    """Common interface for benchmark agent variants."""

    @abstractmethod
    def run(self, task: str) -> AgentResult:
        raise NotImplementedError
