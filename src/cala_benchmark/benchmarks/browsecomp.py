"""Thin integration point for the canonical BrowseComp benchmark.

Do not copy benchmark questions or reimplement its evaluator here.
"""


class BrowseComp:
    name = "browsecomp"

    def tasks(self):
        """Load tasks from the canonical benchmark implementation."""
        raise NotImplementedError

    def evaluate(self, answers):
        """Delegate scoring to the canonical benchmark evaluator."""
        raise NotImplementedError
