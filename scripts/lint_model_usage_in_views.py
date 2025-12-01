#!/usr/bin/env python3
"""Simple linter to spot denylisted model usage within Django view modules."""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

DENYLISTED_MODELS = (
    "Appointment",
    "Clinic",
    "Participant",
    "Symptom",
    "BreastCancerHistoryItem",
)
DENYLISTED_HELPERS = ("get_object_or_404(",)


class Match:
    __slots__ = ("path", "line_number", "target", "line")

    def __init__(self, path, line_number, target, line):
        self.path = path
        self.line_number = line_number
        self.target = target
        self.line = line


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Search Django view modules for direct uses of denylisted model managers."
        )
    )
    parser.add_argument(
        "--apps-dir",
        default="manage_breast_screening",
        help="Relative path to the Django project/apps directory to scan.",
    )
    return parser.parse_args()


def find_view_modules(base_dir):
    """Yield view-like Python modules within the project."""
    for path in base_dir.rglob("*.py"):
        if "tests" in path.parts or "__pycache__" in path.parts:
            continue

        filename = path.name

        if filename == "views.py":
            yield path
            continue

        if filename.endswith("_views.py"):
            yield path
            continue

        if "views" in path.parts[:-1]:
            yield path


def find_matches(paths):
    targets = {
        f"{model_name}.objects": f"{model_name}.objects"
        for model_name in DENYLISTED_MODELS
    }
    for helper in DENYLISTED_HELPERS:
        targets[helper] = helper

    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            for needle, label in targets.items():
                if needle in line:
                    yield Match(
                        path=path,
                        line_number=line_number,
                        target=label,
                        line=line.strip(),
                    )


def main():
    args = parse_args()

    search_root = (REPO_ROOT / args.apps_dir).resolve()

    if not search_root.exists():
        print(
            f"Configured apps directory {search_root} does not exist.",
            file=sys.stderr,
        )
        return 2

    matches = sorted(
        find_matches(find_view_modules(search_root)),
        key=lambda m: (m.path, m.line_number),
    )

    if not matches:
        print("No disallowed references found in view modules.")
        return 0

    print("Disallowed references detected:")
    for match in matches:
        relative_path = match.path.relative_to(REPO_ROOT)
        print(f"- {relative_path}:{match.line_number} -> {match.target}")
        print(f"    {match.line}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
