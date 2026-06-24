# nix-repo-fleet

Nix-packaged tooling for multi-repo fleet triage, PR readiness checks, worktree hygiene, and review prioritization.

## Initial Scope

- Scan many local git repos quickly
- Summarize dirty worktrees and branch drift
- Query GitHub PR state across repos
- Rank merge-ready PRs and stale branches
- Produce machine-readable output for agents

## Status

Early scaffold. See [docs/work-items/README.md](docs/work-items/README.md).

## Current Direction

- implementation language: Python
- output contract: JSON-first
- first executable target: `repo-fleet` placeholder CLI with `repos`, `prs`, and `rank`
