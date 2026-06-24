#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


SCHEMA_VERSION = 1


def run_git(repo_path: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_path), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def find_repos(root: Path) -> list[Path]:
    repos: list[Path] = []
    for current_root, dirnames, filenames in os.walk(root):
        current = Path(current_root)
        if ".git" in dirnames or ".git" in filenames:
            repos.append(current)
            dirnames[:] = []
    return sorted(set(repos))


def count_dirty_files(repo_path: Path) -> int:
    result = run_git(repo_path, ["status", "--porcelain"])
    if result.returncode != 0:
        return -1
    return len([line for line in result.stdout.splitlines() if line.strip()])


def current_branch(repo_path: Path) -> str:
    result = run_git(repo_path, ["symbolic-ref", "--quiet", "--short", "HEAD"])
    if result.returncode == 0:
        return result.stdout.strip()
    detached = run_git(repo_path, ["rev-parse", "--short", "HEAD"])
    if detached.returncode == 0:
        return f"DETACHED:{detached.stdout.strip()}"
    return "UNKNOWN"


def upstream_ahead_behind(repo_path: Path) -> dict[str, int | None]:
    result = run_git(repo_path, ["rev-list", "--left-right", "--count", "@{upstream}...HEAD"])
    if result.returncode != 0:
        return {"ahead": None, "behind": None}
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return {"ahead": None, "behind": None}
    behind, ahead = parts
    return {"ahead": int(ahead), "behind": int(behind)}


def parse_worktree_porcelain(repo_path: Path) -> list[dict[str, str | bool]]:
    result = run_git(repo_path, ["worktree", "list", "--porcelain"])
    if result.returncode != 0:
        return []

    items: list[dict[str, str | bool]] = []
    current: dict[str, str | bool] | None = None
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                items.append(current)
                current = None
            continue
        if line.startswith("worktree "):
            if current:
                items.append(current)
            current = {"path": line.removeprefix("worktree ")}
            continue
        if current is None:
            continue
        if line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True
        else:
            key, _, value = line.partition(" ")
            current[key] = value
    if current:
        items.append(current)
    return items


def git_dir(repo_path: Path) -> str | None:
    result = run_git(repo_path, ["rev-parse", "--git-dir"])
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def common_dir(repo_path: Path) -> str | None:
    result = run_git(repo_path, ["rev-parse", "--git-common-dir"])
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def summarize_repo(repo_path: Path) -> dict:
    dirty_file_count = count_dirty_files(repo_path)
    worktrees = parse_worktree_porcelain(repo_path)
    summary = {
        "repo_path": str(repo_path),
        "repo_name": repo_path.name,
        "git_dir": git_dir(repo_path),
        "git_common_dir": common_dir(repo_path),
        "current_branch": current_branch(repo_path),
        "is_dirty": dirty_file_count > 0,
        "dirty_file_count": dirty_file_count,
        "tracking": upstream_ahead_behind(repo_path),
        "worktrees": worktrees,
        "classification": "unknown",
        "registered_owner_repo_path": None,
    }
    return summary


def classify_repos(root: Path, summaries: list[dict]) -> list[dict]:
    registered_paths: dict[str, str] = {}
    primary_paths: set[str] = set()

    for summary in summaries:
        for idx, worktree in enumerate(summary["worktrees"]):
            worktree_path = worktree.get("path")
            if not isinstance(worktree_path, str):
                continue
            if idx == 0:
                primary_paths.add(worktree_path)
            registered_paths[worktree_path] = summary["repo_path"]

    for summary in summaries:
        repo_path = summary["repo_path"]
        owner_repo = registered_paths.get(repo_path)
        if repo_path in primary_paths:
            summary["classification"] = "primary_checkout"
        elif owner_repo:
            summary["classification"] = "registered_worktree"
            summary["registered_owner_repo_path"] = owner_repo
        elif repo_path.startswith("/tmp/"):
            summary["classification"] = "ad_hoc_temp_clone"
        else:
            summary["classification"] = "standalone_clone"

    return summaries


def repos_command(args: argparse.Namespace) -> int:
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        payload = {
            "schema_version": SCHEMA_VERSION,
            "tool": "nix-repo-fleet",
            "subcommand": "repos",
            "status": "error",
            "message": f"Root path does not exist: {root}",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    repos = find_repos(root)
    summaries = [summarize_repo(repo_path) for repo_path in repos]
    summaries = classify_repos(root, summaries)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": "nix-repo-fleet",
        "subcommand": "repos",
        "status": "ok",
        "root": str(root),
        "repo_count": len(summaries),
        "repos": summaries,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def placeholder_command(subcommand: str) -> int:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": "nix-repo-fleet",
        "subcommand": subcommand,
        "status": "placeholder",
        "message": f"{subcommand} is not implemented yet",
        "supported_subcommands": ["repos", "prs", "rank"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repo-fleet")
    subparsers = parser.add_subparsers(dest="subcommand")

    repos_parser = subparsers.add_parser("repos")
    repos_parser.add_argument("--root", default=".")

    subparsers.add_parser("prs")
    subparsers.add_parser("rank")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    subcommand = args.subcommand or "repos"

    if subcommand == "repos":
        return repos_command(args)
    if subcommand == "prs":
        return placeholder_command("prs")
    if subcommand == "rank":
        return placeholder_command("rank")

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
