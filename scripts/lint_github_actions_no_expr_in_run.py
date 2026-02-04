#!/usr/bin/env python3
"""Check for expression interpolation in GitHub Actions run blocks."""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

TARGET_DIRS = [
    REPO_ROOT / ".github" / "workflows",
    REPO_ROOT / ".github" / "actions",
]

RUN_LINE_RE = re.compile(r"^(?P<indent>\s*)run:\s*(?P<rest>.*)$")
BLOCK_SCALAR_RE = re.compile(r"^[|>][-+]?\s*$")
EXPR_RE = re.compile(r"\$\{\{[^}]+\}\}")


@dataclass
class Violation:
    path: Path
    line_number: int
    line: str


def find_yaml_files():
    """Yield YAML files within the target directories."""
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for pattern in ("*.yml", "*.yaml"):
            yield from base.rglob(pattern)


def is_indented_more(line: str, indent: str) -> bool:
    if not line.strip():
        return False
    return line.startswith(indent + " ") or line.startswith(indent + "\t")


def find_violations(paths):
    """Yield violations found in the given paths."""
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue

        i = 0
        while i < len(lines):
            line = lines[i]
            match = RUN_LINE_RE.match(line)
            if not match:
                i += 1
                continue

            indent = match.group("indent")
            rest = match.group("rest").rstrip()

            # Inline run: command
            if rest and not BLOCK_SCALAR_RE.match(rest.strip()):
                if EXPR_RE.search(rest):
                    yield Violation(
                        path=path,
                        line_number=i + 1,
                        line=rest.strip(),
                    )
                i += 1
                continue

            # Block scalar run: | or >
            i += 1
            while i < len(lines) and is_indented_more(lines[i], indent):
                if EXPR_RE.search(lines[i]):
                    yield Violation(
                        path=path,
                        line_number=i + 1,
                        line=lines[i].strip(),
                    )
                i += 1


def main():
    violations = sorted(
        find_violations(find_yaml_files()),
        key=lambda v: (v.path, v.line_number),
    )

    if not violations:
        print("No expression interpolations found in run blocks.")
        return 0

    print("GitHub Actions script-injection guard failed:")
    for violation in violations:
        relative_path = violation.path.relative_to(REPO_ROOT)
        print(f"- {relative_path}:{violation.line_number}")
        print(f"    {violation.line}")

    print(
        "\nMove ${{ ... }} expressions into env/inputs and reference shell variables instead."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
