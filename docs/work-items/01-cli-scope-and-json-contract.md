# 01 CLI Scope And JSON Contract

Status: in-progress

## Goal

Define the first stable command surface and output schema for the tool.

## Deliverables

- choose implementation language
- define CLI subcommands and flags
- document JSON schema for local repo summary and PR readiness summary
- add a minimal executable that returns placeholder structured output

## Notes

- optimize for agent consumption first
- avoid premature TUI work
- keep the schema versioned from the start

## Progress

- implementation language chosen: Python
- initial CLI shape defined in `docs/cli-contract.md`
- placeholder executable scaffolded in `src/repo_fleet_cli.py`
