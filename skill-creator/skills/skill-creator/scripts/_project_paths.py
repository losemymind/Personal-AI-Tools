"""Locate this skill's root directory (self-contained).

Works whether this module is executed directly from the skill directory or
imported from elsewhere. The skill-creator skill never depends on a host
repository: its root is the directory that contains scripts/, i.e. the
parent of this file's directory.
"""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def find_skill_root(source_file: str | Path) -> Path:
    """Return the skill root (the directory containing scripts/) for source_file.

    Scripts live in <skill-root>/scripts/, so the skill root is the parent
    of the scripts directory. No host/git-repository dependency.
    """
    return Path(source_file).resolve().parent.parent


def add_scripts_to_path() -> None:
    """Allow direct imports of sibling modules from this scripts directory."""
    sys.path.insert(0, str(SCRIPT_DIR))
