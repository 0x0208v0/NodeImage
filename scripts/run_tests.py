#!/usr/bin/env python3
"""Test runner script for NodeImage."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == '__main__':
    # Run pytest with the tests directory
    tests_dir = project_root / 'tests'

    # Run tests with verbose output and exit on first failure for quick feedback
    exit_code = pytest.main(
        [
            str(tests_dir),
            '-v',  # verbose output
            '--tb=short',  # shorter traceback format
            '--strict-markers',  # treat unregistered markers as errors
            '--strict-config',  # treat config errors as errors
        ]
    )

    sys.exit(exit_code)
