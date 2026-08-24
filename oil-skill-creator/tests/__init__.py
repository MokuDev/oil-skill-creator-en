"""Tests for oil-skill-creator's deterministic helper programs.

The test modules import `scripts.*` from the Skill root. Make that root
importable regardless of the working directory the tests are started from.
"""

import sys
from pathlib import Path

_SKILL_ROOT = str(Path(__file__).resolve().parent.parent)
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)
