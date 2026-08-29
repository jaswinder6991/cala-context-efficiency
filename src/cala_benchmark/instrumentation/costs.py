from dataclasses import dataclass


@dataclass
class Cost:
    """Estimated run cost; provider-specific pricing is configured later."""

    llm_usd: float = 0.0
    retrieval_usd: float = 0.0

    @property
    def total_usd(self) -> float:
        return self.llm_usd + self.retrieval_usd
