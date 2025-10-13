#!/usr/bin/env bash

set -euo pipefail

if ! command -v rg >/dev/null 2>&1; then
  echo "ripgrep (rg) is required to run this linter." >&2
  exit 2
fi

cd "$(git rev-parse --show-toplevel)"

declare -a view_files=()
while IFS= read -r file; do
  view_files+=("$file")
done < <(rg --files -g '*views*.py' --glob '!**/tests/**' manage_breast_screening)

if [[ ${#view_files[@]} -eq 0 ]]; then
  exit 0
fi

matches=0

direct_model_pattern='\b[A-Z][A-Za-z0-9_]*\.objects\b'
if results=$(rg --no-messages --with-filename --line-number --color never "$direct_model_pattern" "${view_files[@]}" || true); then
  if [[ -n "$results" ]]; then
    echo "Direct model access detected. Use repository classes in views instead:" >&2
    echo "$results" >&2
    echo >&2
    matches=1
  fi
fi

model_import_pattern='from.*models.*import'
if results=$(rg --no-messages --with-filename --line-number --color never "$model_import_pattern" "${view_files[@]}" || true); then
  if [[ -n "$results" ]]; then
    echo "Model imports detected in views. Replace with repository usage:" >&2
    echo "$results" >&2
    echo >&2
    matches=1
  fi
fi

if [[ $matches -ne 0 ]]; then
  exit 1
fi

exit 0
