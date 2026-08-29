"""Run a BrowseComp experiment arm through Inspect AI."""

from __future__ import annotations

import sys
from pathlib import Path

src = Path(__file__).resolve().parents[1] / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from cala_benchmark.cli import main

if __name__ == "__main__":
    main()
