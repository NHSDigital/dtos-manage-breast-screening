#!/usr/bin/env bash
#
# Lightweight provider scoping linter powered by ripgrep.
#
# Flags occurrences of provider-scoped models that do not call
# `.for_provider()` immediately after `.objects`, and any usage of
# `get_object_or_404` / `get_list_or_404`.

set -euo pipefail

if ! command -v rg >/dev/null 2>&1; then
  echo "lint_provider_scoping_grep: ripgrep (rg) is required" >&2
  exit 1
fi

if ! rg --pcre2 --version >/dev/null 2>&1; then
  echo "lint_provider_scoping_grep: ripgrep must be built with PCRE2 support" >&2
  exit 1
fi

PROVIDER_MODELS_REGEX='(Clinic|ClinicSlot|Appointment|Participant)'
DEFAULT_TARGETS=(manage_breast_screening)

targets=("$@")
if [ ${#targets[@]} -eq 0 ]; then
  targets=("${DEFAULT_TARGETS[@]}")
fi

status=0

echo "Checking provider scoping with ripgrep…" >&2

# Detect `.objects` chains missing `.for_provider()` as the first call
if rg --multiline --multiline-dotall --pcre2 -n \
  "${PROVIDER_MODELS_REGEX}\.objects(?!\s*\.for_provider\()" \
  "${targets[@]}" >/tmp/provider_scope_objects.out; then
  echo "PS001 (grep): found manager usage without .for_provider()" >&2
  cat /tmp/provider_scope_objects.out >&2
  status=1
fi

# Detect banned shortcuts
if rg --multiline --pcre2 -n \
  '\bget_(object|list)_or_404\s*\(' \
  "${targets[@]}" >/tmp/provider_scope_shortcuts.out; then
  echo "PS002 (grep): found provider-agnostic shortcut usage" >&2
  cat /tmp/provider_scope_shortcuts.out >&2
  status=1
fi

rm -f /tmp/provider_scope_objects.out /tmp/provider_scope_shortcuts.out

exit $status
