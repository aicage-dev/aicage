#!/usr/bin/env python3
"""Write the non-proxy integration-test matrix to GitHub Actions output."""

import contextlib
import io
import json
import os
from pathlib import Path

import pytest


def main() -> None:
    """Collect pytest node IDs and write them as a GitHub Actions matrix."""
    output_buffer = io.StringIO()
    with contextlib.redirect_stdout(output_buffer):
        exit_code = pytest.main(
            ["--collect-only", "-q", "-m", "integration and not proxy_integration"]
        )
    if exit_code != pytest.ExitCode.OK:
        raise SystemExit(exit_code)
    output = output_buffer.getvalue()
    node_ids = [line for line in output.splitlines() if "::" in line]
    matrix = {"include": [{"test": node_id} for node_id in node_ids]}
    github_output = Path(os.environ["GITHUB_OUTPUT"])
    with github_output.open("a", encoding="utf-8") as handle:
        handle.write(f"matrix={json.dumps(matrix)}\n")


if __name__ == "__main__":
    main()
