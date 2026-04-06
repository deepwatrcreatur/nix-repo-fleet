# Agent Prompts

## Prompt 1

Implement the initial CLI contract for `nix-repo-fleet`.

Requirements:
- define subcommands for `repos`, `prs`, and `rank`
- produce JSON output first, human formatting second
- keep the implementation language decision explicit in the task output

## Prompt 2

Build the local repo scanner.

Requirements:
- detect git repos, branch names, dirty status, and registered worktrees
- handle missing or non-git directories safely
- return structured output suitable for later PR correlation

## Prompt 3

Add GitHub PR readiness integration.

Requirements:
- query open PRs for a user or repo set
- normalize mergeability, review state, and checks into a compact schema
- avoid mixing rendering logic with API access logic
