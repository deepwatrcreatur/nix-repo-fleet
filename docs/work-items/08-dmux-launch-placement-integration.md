# 08 Dmux Launch Placement Integration

Status: ready

## Goal

Go beyond "block shared checkout" and define the next slice where `dmux`-style
launches can be placed into the correct linked worktree deliberately, using the
repo/worktree state surfaced by this tooling.

## Deliverables

- define the minimum data needed to place a launch safely:
  - canonical branch
  - existing linked worktrees
  - stale vs active ownership signals
  - recommended target worktree
- distinguish:
  - inspect-only launch from shared checkout
  - mutation launch in a linked worktree
  - blocked launch from an unsafe location
- document the handoff boundary between `nix-repo-fleet` state and `dmux`
  wrapper behavior
- keep the slice bounded to placement/preflight rather than full lifecycle
  automation

## Notes

- this item is the missing bridge between repo hygiene state and actual wrapper
  launch decisions
- do not expand into a full TUI/orchestration shell here
