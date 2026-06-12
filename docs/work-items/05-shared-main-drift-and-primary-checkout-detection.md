# 05 Shared Main Drift And Primary Checkout Detection

Status: ready

## Goal

Detect the cases where a repo's shared or primary materialized checkout is no
longer on branch `main` (or another configured canonical branch), and surface
that as a first-class hygiene problem rather than burying it in generic branch
state.

## Deliverables

- define a machine-readable notion of a repo's shared/primary checkout
- detect when that checkout is on a feature branch instead of the canonical
  branch
- distinguish:
  - healthy linked worktree usage
  - intentionally detached/publish worktrees
  - and an accidentally repurposed shared `main` checkout
- emit explicit drift reasons in JSON output

## Notes

- this item is about **shared-checkout drift detection**, not about automatic
  repair yet
- optimize for the exact failure mode where agents are pointed at `/main` but
  `/main` is not actually on `main`
