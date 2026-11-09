#!/usr/bin/env python3
"""Write the non-proxy integration-test matrix to GitHub Actions output."""

import contextlib
import io
import json
import os
import shlex
from pathlib import Path

import pytest

# TEST-WIP(Task 42): keep CI focused on credential forwarding while its existing
# integration failures are diagnosed. Remove this filter before merging upstream.
_TEST_WIP_NODE_IDS = {
    "tests/aicage/integration/test_gpg_agent.py::test_gpg_agent_signs_through_direct_agent",
    "tests/aicage/integration/test_gpg_agent.py::test_gpg_agent_signs_through_sidecar",
    (
        "tests/aicage/integration/test_gpg_agent.py::"
        "test_protected_gpg_key_reloads_after_restart_and_rejects_missing_secret"
    ),
    "tests/aicage/integration/test_ssh_agent.py::test_ssh_agent_is_available_in_container",
    (
        "tests/aicage/integration/test_ssh_agent.py::"
        "test_protected_ssh_key_setup_reloads_after_restart_and_rejects_missing_secret"
    ),
}


def main() -> None:
    """Collect pytest node IDs and write them as a GitHub Actions matrix."""
    pytest_filter = os.environ.get("PYTEST_FILTER", "").strip()
    command = ["--collect-only", "-q", "-m", "integration and not proxy_integration"]
    if pytest_filter:
        command.extend(shlex.split(pytest_filter))
    output_buffer = io.StringIO()
    with contextlib.redirect_stdout(output_buffer):
        exit_code = pytest.main(command)
    if exit_code != pytest.ExitCode.OK:
        raise SystemExit(exit_code)
    output = output_buffer.getvalue()
    node_ids = [line for line in output.splitlines() if line in _TEST_WIP_NODE_IDS]
    matrix = {"include": [{"test": node_id} for node_id in node_ids]}
    github_output = Path(os.environ["GITHUB_OUTPUT"])
    with github_output.open("a", encoding="utf-8") as handle:
        handle.write(f"matrix={json.dumps(matrix)}\n")


if __name__ == "__main__":
    main()
