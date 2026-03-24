<!-- Provide a brief, sentence-case description of the change in the PR title, eg "Update appointment show page" -->

## Description

<!-- Add screenshots if there are any UI updates. -->

## Jira link

## Review notes

<!-- Add notable context, discussion items, and anything else that would be helpful for a reviewer to know. -->

## Review checklist

- [ ] Check database queries are correctly scoped to current_provider
- [ ] If this changes the gateway API (`/api/v1/`), confirm whether it is a breaking change — if so, a new major version (`/api/v2/`) is required (see [ADR-006](../docs/adr/ADR-006-Gateway_API_versioning_strategy.md))
