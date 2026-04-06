# 02 Local Repo Scan And Worktree Summary

Status: ready

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
