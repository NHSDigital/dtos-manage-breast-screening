# Dependabot Reviewer CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a single-file interactive CLI tool at `scripts/dependabot_reviewer.py` that lists open dependabot PRs with build/review/merge status, then lets the user approve or merge selected PRs.

**Architecture:** Single Python file using only stdlib. Shells out to `gh` for all GitHub operations. Interactive loop: display table → prompt action → prompt PR numbers → execute.

**Tech Stack:** Python 3.14+, `gh` CLI, `subprocess`, `json`, `argparse`, `dataclasses`, `time`

---

Run with: `uv run python scripts/dependabot_reviewer.py`
