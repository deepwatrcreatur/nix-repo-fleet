# 06 Stale Worktree And Branch Debris Heuristics

Status: ready

## Goal

Identify likely stale linked worktrees and branch debris so agents and operators
can tell the difference between active ownership and abandoned residue.

## Deliverables

- define heuristics for likely-stale worktrees, such as:
  - branch no longer checked out anywhere meaningful
  - no recent commit or push activity
  - detached publish worktree with no current purpose
  - worktree path exists but no recent ownership signal
- surface likely cleanup candidates in JSON output
- emit concise reasons instead of a single vague "stale" label
- keep the classification explainable and reversible

## Notes

- do not auto-delete worktrees in this slice
- optimize for reducing false ownership signals and stale-success promotion
