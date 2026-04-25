# 03 GitHub PR Readiness Integration

Status: done

## Goal

Pull PR readiness data from GitHub and normalize it for ranking and merge suggestions.

## Deliverables

- support querying by owner and optional repo filter
- normalize mergeability, merge-state status, review decision, and checks
- capture enough metadata to distinguish "ready", "waiting on bots", and "blocked"

## Notes

- prefer `gh` command integration first
- design the adapter so direct API usage can be swapped in later

## Progress

- `repo-fleet prs` now supports `--owner` or `--repo`
- current implementation uses `gh search prs` plus `gh pr view` normalization
- PRs are categorized into `ready_or_needs_human_review`, `waiting_on_checks`, `blocked_checks`, `blocked_conflicts`, `blocked_reviews`, or `unknown`
