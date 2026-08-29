from dataclasses import dataclass


@dataclass
class Comparison:
    """Aggregate results from the canonical evaluator and execution traces."""

    baseline: dict
    treatment: dict

    def cost_per_success(self, result: dict) -> float | None:
        successes = result.get("successes", 0)
        if not successes:
            return None
        return result.get("cost_usd", 0.0) / successes
