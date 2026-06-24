# CLI Contract

## Decision

Use Python for the initial implementation.

Reasons:

- strong JSON and subprocess ergonomics
- fast enough for local repo and `gh` orchestration
- easy to package in a small flake

## Commands

### `repo-fleet repos`

Summarize local repository state beneath a root path.

Primary fields:

- `repo_path`
- `git_dir`
- `current_branch`
- `is_dirty`
- `dirty_file_count`
- `worktrees`
- `classification`

### `repo-fleet prs`

Summarize open PR state across one or more repos.

Primary fields:

- `repository`
- `number`
- `title`
- `url`
- `mergeable`
- `merge_state_status`
- `review_decision`
- `checks_summary`
- `category`

### `repo-fleet rank`

Produce a ranked action list derived from local repo state and PR state.

Primary fields:

- `rank`
- `action`
- `reason`
- `target_kind`
- `target_ref`
- `confidence`

## JSON Rules

- JSON is the default output mode.
- Every payload includes `schema_version`.
- Human-readable rendering is a later layer over the same internal model.
