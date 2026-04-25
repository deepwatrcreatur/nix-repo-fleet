# 02 Local Repo Scan And Worktree Summary

Status: done

## Goal

Scan a directory of repos and summarize local git state with enough detail to support cleanup and merge workflows.

## Deliverables

- detect repos under a root path
- capture current branch, ahead/behind state when available, dirty files count, and worktree list
- distinguish registered worktrees from ad hoc temp clones
- emit JSON output

## Notes

- do not assume all directories are git repos
- prefer fast local commands and bounded output

## Progress

- `repo-fleet repos --root <path>` implemented in `src/repo_fleet_cli.py`
- current output includes branch, dirty count, upstream drift, worktrees, and classification
- temporary standalone clones under `/tmp` are classified separately from registered worktrees

## Outcome

The local repo scanner now emits structured JSON that is already useful for worktree cleanup and fleet hygiene.
