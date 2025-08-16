"""Pytest configuration for local imports.

Ensure the repository root is on sys.path so tests can import the `app` package
when running pytest from the repo root or from other working directories.
"""
import sys
from pathlib import Path

# Insert repo root (two levels up from tests/) at front of sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
