#!/usr/bin/env python3
"""Write the non-proxy integration-test matrix to GitHub Actions output."""

import json
import os
import subprocess
from pathlib import Path


def main() -> None:
    """Collect pytest node IDs and write them as a GitHub Actions matrix."""
    output = subprocess.check_output(
        ["pytest", "--collect-only", "-q", "-m", "integration and not proxy_integration"],
        text=True,
    )
    node_ids = [line for line in output.splitlines() if "::" in line]
    matrix = {"include": [{"test": node_id} for node_id in node_ids]}
    github_output = Path(os.environ["GITHUB_OUTPUT"])
    with github_output.open("a", encoding="utf-8") as handle:
        handle.write(f"matrix={json.dumps(matrix)}\n")


if __name__ == "__main__":
    main()
