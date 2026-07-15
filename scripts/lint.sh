#!/usr/bin/env bash
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

# YAML
yamllint .

# Markdown
pymarkdown \
  --config .pymarkdown.json scan \
  --recurse \
  --exclude '**/.venv*/**' \
  .

# ruff (Python)
ruff check .

# pyright (Python)
pyright .

# Ignore generated version metadata from setuptools-scm.
if rg_output=$(rg -n --glob '*.py' --glob '!src/*/_version.py' '__all__' src); then
  printf '%s\n' "$rg_output"
  echo "Found __all__ usage in src; remove it to satisfy visibility checks."
  exit 1
else
  rg_status=$?
  if [[ $rg_status -ne 1 ]]; then
    exit $rg_status
  fi
fi

# Shellcheck
mapfile -t shell_scripts < <(find . -type f -name '*.sh' -not -path './.venv/*' | sort)

if [[ ${#shell_scripts[@]} -gt 0 ]]; then
  echo "Validate shell scripts with bash -n"
  for script in "${shell_scripts[@]}"; do
    bash -n "${script}"
  done

  echo "Run shellcheck"
  shellcheck -x "${shell_scripts[@]}"
fi

# flake8
flake8 .

# bandit
bandit --quiet -c .bandit.yml -r src 2>/dev/null
