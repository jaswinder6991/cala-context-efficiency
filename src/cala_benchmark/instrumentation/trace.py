from dataclasses import dataclass, field
from typing import Any


@dataclass
class Trace:
    """Normalized execution trace collected without owning evaluation."""

    events: list[dict[str, Any]] = field(default_factory=list)

    def add(self, event: dict[str, Any]) -> None:
        self.events.append(event)
