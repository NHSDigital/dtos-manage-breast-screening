#!/usr/bin/env python3
"""Interactive CLI to review, approve, and merge dependabot pull requests."""

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass


@dataclass
class PullRequest:
    number: int
    title: str
    check_status: str  # computed from statusCheckRollup
    review_decision: str  # formatted reviewDecision
    mergeable_display: str  # human-readable mergeability
    can_merge: bool  # True only when mergeStateStatus == "CLEAN"


def run_gh_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a gh CLI command and return the result."""
    return subprocess.run(
        ["gh", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def compute_check_status(checks: list[dict]) -> str:
    """Compute an overall check status from statusCheckRollup data."""
    if not checks:
        return "— No checks"

    has_failure = False
    has_action_required = False
    has_pending = False

    for check in checks:
        status = check.get("status", "").upper()
        conclusion = check.get("conclusion", "").upper()

        if status in ("QUEUED", "IN_PROGRESS", "PENDING", "WAITING"):
            has_pending = True
        elif conclusion in ("FAILURE", "TIMED_OUT", "STARTUP_FAILURE"):
            has_failure = True
        elif conclusion in ("ACTION_REQUIRED", "STALE", "CANCELLED"):
            has_action_required = True
        # SUCCESS / SKIPPED / NEUTRAL are implicitly passing — no flag needed

    if has_failure:
        return "✗ Failing"
    if has_action_required:
        return "⚠ Action required"
    if has_pending:
        return "⊙ Pending"
    return "✓ Passing"


def format_review_decision(decision: str | None) -> str:
    """Format a GitHub reviewDecision enum value for display."""
    match (decision or "").upper():
        case "APPROVED":
            return "✓ Approved"
        case "CHANGES_REQUESTED":
            return "✗ Changes requested"
        case "REVIEW_REQUIRED":
            return "⊙ Review required"
        case _:
            return "—"


def format_mergeability(merge_state: str) -> tuple[str, bool]:
    """
    Return a (display_string, can_merge) tuple.

    can_merge is True only when merge_state is CLEAN.
    """
    match merge_state.upper():
        case "CLEAN":
            return "✓ Mergeable", True
        case "BEHIND":
            return "⚠ Behind", False
        case "BLOCKED":
            return "✗ Blocked", False
        case "DIRTY":
            return "✗ Conflicts", False
        case "DRAFT":
            return "✗ Draft", False
        case "UNSTABLE":
            return "⚠ Unstable", False
        case _:
            return "? Unknown", False


def fetch_dependabot_prs(
    state: str = "open", limit: int = 100
) -> list[PullRequest]:  # gh supports up to 1000
    """Fetch dependabot PRs and return parsed PullRequest objects."""
    result = run_gh_command(
        [
            "pr",
            "list",
            "--state",
            state,
            "--json",
            "number,title,headRefName,statusCheckRollup,reviewDecision,mergeable,mergeStateStatus",
            "--limit",
            str(limit),
        ]
    )

    if result.returncode != 0:
        print(result.stderr.strip() or "Failed to list pull requests.", file=sys.stderr)
        sys.exit(result.returncode)

    try:
        items = json.loads(result.stdout or "[]")
    except json.JSONDecodeError as exc:
        print(f"Could not parse gh output: {exc}", file=sys.stderr)
        sys.exit(1)

    pull_requests = []

    for item in items:
        if not item.get("headRefName", "").startswith("dependabot/"):
            continue

        mergeable_display, can_merge = format_mergeability(
            item.get("mergeStateStatus") or "",
        )

        pull_requests.append(
            PullRequest(
                number=item.get("number"),
                title=item.get("title", ""),
                check_status=compute_check_status(item.get("statusCheckRollup") or []),
                review_decision=format_review_decision(item.get("reviewDecision")),
                mergeable_display=mergeable_display,
                can_merge=can_merge,
            )
        )

    return pull_requests


def display_pull_requests(pull_requests: list[PullRequest]) -> None:
    """Print a formatted table of pull requests."""
    if not pull_requests:
        print("No open dependabot pull requests found.")
        return

    col_pr = 8
    col_title = 52
    col_checks = 18
    col_review = 22

    header = (
        f"{'PR':<{col_pr}}"
        f"{'Title':<{col_title}}"
        f"{'Checks':<{col_checks}}"
        f"{'Review':<{col_review}}"
        f"Mergeable"
    )
    print(header)
    print("-" * len(header))

    for pr in pull_requests:
        title = (
            pr.title if len(pr.title) <= col_title else pr.title[: col_title - 1] + "…"
        )
        print(
            f"#{pr.number:<{col_pr - 1}}"
            f"{title:<{col_title}}"
            f"{pr.check_status:<{col_checks}}"
            f"{pr.review_decision:<{col_review}}"
            f"{pr.mergeable_display}"
        )


def prompt_action() -> str:
    """Prompt the user to choose an action. Returns 'a', 'm', or 'q'."""
    while True:
        choice = input("\nAction: (a)pprove / (m)erge / (q)uit: ").strip().lower()
        if choice in ("a", "m", "q"):
            return choice
        print("Please enter 'a', 'm', or 'q'.")


def parse_pr_selection(raw: str, available: list[int]) -> list[int]:
    """
    Parse a space/comma-separated string of PR numbers.

    Validates each number against the available list and deduplicates.
    """
    selected: list[int] = []

    for token in raw.replace(",", " ").split():
        try:
            number = int(token)
        except ValueError:
            print(f"Ignoring invalid input: {token!r}")
            continue

        if number not in available:
            print(f"PR #{number} is not in the listed results; skipping.")
            continue

        if number not in selected:
            selected.append(number)

    return selected


def approve_pr(number: int) -> bool:
    """Approve a pull request. Returns True on success."""
    print(f"Approving #{number}...", end=" ", flush=True)
    result = run_gh_command(["pr", "review", str(number), "--approve"])

    if result.returncode == 0:
        print("✓")
        return True

    print("✗")
    print(result.stderr.strip() or f"Failed to approve #{number}.", file=sys.stderr)
    return False


MERGE_DELAY_SECONDS = 5


def merge_prs(prs_by_number: dict[int, PullRequest], selections: list[int]) -> None:
    """
    Merge selected PRs in order.

    Skips non-mergeable PRs with a warning.
    Waits MERGE_DELAY_SECONDS between each successful merge.
    """
    merged_count = 0

    for number in selections:
        pr = prs_by_number[number]

        if not pr.can_merge:
            print(
                f"Skipping #{number} ({pr.mergeable_display}) — not currently mergeable."
            )
            continue

        if merged_count > 0:
            print(f"Waiting {MERGE_DELAY_SECONDS}s before next merge...")
            time.sleep(MERGE_DELAY_SECONDS)

        print(f"Merging #{number}...", end=" ", flush=True)
        result = run_gh_command(
            ["pr", "merge", str(number), "--merge", "--delete-branch"]
        )

        if result.returncode == 0:
            print("✓")
            merged_count += 1
        else:
            print("✗")
            print(
                result.stderr.strip() or f"Failed to merge #{number}.", file=sys.stderr
            )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Review, approve, and merge dependabot pull requests."
    )
    parser.add_argument(
        "--state",
        default="open",
        choices=("open", "closed", "all"),
        help="Filter pull requests by state (default: open).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of pull requests to fetch (default: 100).",
    )
    args = parser.parse_args()

    print("Fetching dependabot PRs...")
    pull_requests = fetch_dependabot_prs(state=args.state, limit=args.limit)
    print()
    display_pull_requests(pull_requests)

    if not pull_requests:
        return 0

    action = prompt_action()

    if action == "q":
        return 0

    available = [pr.number for pr in pull_requests]
    raw = input("PR numbers (space or comma separated, blank to abort): ").strip()

    if not raw:
        print("Aborted.")
        return 0

    selections = parse_pr_selection(raw, available)

    if not selections:
        print("No valid PR numbers provided.")
        return 0

    if action == "a":
        for number in selections:
            approve_pr(number)
    elif action == "m":
        prs_by_number = {pr.number: pr for pr in pull_requests}
        merge_prs(prs_by_number, selections)

    return 0


if __name__ == "__main__":
    sys.exit(main())
