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


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
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


def summarize_checks(status_check_rollup: list[dict]) -> dict:
    summary = {
        "total": len(status_check_rollup),
        "success": 0,
        "failed": 0,
        "pending": 0,
        "skipped": 0,
    }
    for item in status_check_rollup:
        conclusion = item.get("conclusion")
        state = item.get("state")
        status = item.get("status")
        if conclusion == "SUCCESS" or state == "SUCCESS":
            summary["success"] += 1
        elif conclusion in {"FAILURE", "TIMED_OUT", "CANCELLED", "STARTUP_FAILURE"} or state in {"FAILURE", "ERROR"}:
            summary["failed"] += 1
        elif conclusion == "SKIPPED":
            summary["skipped"] += 1
        elif state == "PENDING" or status in {"IN_PROGRESS", "QUEUED", "WAITING"}:
            summary["pending"] += 1
        else:
            summary["pending"] += 1
    return summary


def categorize_pr(pr: dict) -> str:
    checks = pr["checks_summary"]
    if pr["mergeable"] == "CONFLICTING":
        return "blocked_conflicts"
    if checks["failed"] > 0:
        return "blocked_checks"
    if checks["pending"] > 0:
        return "waiting_on_checks"
    if pr["mergeable"] == "MERGEABLE" and pr["merge_state_status"] in {"CLEAN", "HAS_HOOKS", "UNKNOWN"}:
        if pr["review_decision"] == "CHANGES_REQUESTED":
            return "blocked_reviews"
        if pr["review_decision"] in {"APPROVED", ""}:
            return "ready_or_needs_human_review"
    return "unknown"


def gh_json(args: list[str]) -> tuple[object | None, str | None]:
    result = run_command(args)
    if result.returncode != 0:
        return None, result.stderr.strip() or result.stdout.strip() or "command failed"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON output: {exc}"


def fetch_pr_details(repo: str, number: int) -> dict:
    data, error = gh_json(
        [
            "gh",
            "pr",
            "view",
            str(number),
            "-R",
            repo,
            "--json",
            "number,title,url,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup",
        ]
    )
    if error is not None or not isinstance(data, dict):
        return {
            "repository": repo,
            "number": number,
            "status": "error",
            "error": error or "unknown error",
        }

    checks_summary = summarize_checks(data.get("statusCheckRollup", []))
    pr = {
        "repository": repo,
        "number": data.get("number"),
        "title": data.get("title"),
        "url": data.get("url"),
        "mergeable": data.get("mergeable"),
        "merge_state_status": data.get("mergeStateStatus"),
        "review_decision": data.get("reviewDecision") or "",
        "checks_summary": checks_summary,
        "status": "ok",
    }
    pr["category"] = categorize_pr(pr)
    return pr


def search_owner_prs(owner: str, state: str, limit: int) -> tuple[list[dict], str | None]:
    data, error = gh_json(
        [
            "gh",
            "search",
            "prs",
            "--owner",
            owner,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number,repository,title,url",
        ]
    )
    if error is not None or not isinstance(data, list):
        return [], error or "unknown error"

    details: list[dict] = []
    for item in data:
        repo = item.get("repository", {}).get("nameWithOwner")
        number = item.get("number")
        if not isinstance(repo, str) or not isinstance(number, int):
            continue
        details.append(fetch_pr_details(repo, number))
    return details, None


def list_repo_prs(repo: str, state: str, limit: int) -> tuple[list[dict], str | None]:
    data, error = gh_json(
        [
            "gh",
            "pr",
            "list",
            "-R",
            repo,
            "--state",
            state,
            "--limit",
            str(limit),
            "--json",
            "number",
        ]
    )
    if error is not None or not isinstance(data, list):
        return [], error or "unknown error"

    details = []
    for item in data:
        number = item.get("number")
        if not isinstance(number, int):
            continue
        details.append(fetch_pr_details(repo, number))
    return details, None


def prs_command(args: argparse.Namespace) -> int:
    if not args.owner and not args.repo:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "tool": "nix-repo-fleet",
            "subcommand": "prs",
            "status": "error",
            "message": "Provide --owner or --repo",
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1

    if args.repo:
        prs, error = list_repo_prs(args.repo, args.state, args.limit)
    else:
        prs, error = search_owner_prs(args.owner, args.state, args.limit)

    status = "ok" if error is None else "partial"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": "nix-repo-fleet",
        "subcommand": "prs",
        "status": status,
        "owner": args.owner,
        "repo": args.repo,
        "state": args.state,
        "pr_count": len(prs),
        "prs": prs,
    }
    if error is not None:
        payload["error"] = error
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if status == "ok" else 1


def rank_command(args: argparse.Namespace) -> int:
    # 1. Fetch Repos
    root = Path(args.root).expanduser().resolve()
    repos = []
    if root.exists():
        found = find_repos(root)
        summaries = [summarize_repo(repo_path) for repo_path in found]
        repos = classify_repos(root, summaries)

    # 2. Fetch PRs
    prs = []
    if args.owner or args.repo:
        if args.repo:
            prs, _ = list_repo_prs(args.repo, "open", 50)
        else:
            prs, _ = search_owner_prs(args.owner, "open", 50)

    # 3. Generate Recommendations
    recommendations = []

    # PR Recommendations
    for pr in prs:
        if pr.get("status") != "ok":
            continue

        rec = {
            "type": "pr",
            "repository": pr["repository"],
            "number": pr["number"],
            "title": pr["title"],
            "url": pr["url"],
            "score": 0,
            "action": "unknown",
            "reason": "",
        }

        category = pr.get("category")
        if category == "ready_or_needs_human_review":
            rec["score"] = 10
            rec["action"] = "merge"
            rec["reason"] = "PR is clean and approved (or needs final human check)"
        elif category == "waiting_on_checks":
            rec["score"] = 5
            rec["action"] = "wait"
            rec["reason"] = "Waiting for CI checks to complete"
        elif category == "blocked_reviews":
            rec["score"] = 2
            rec["action"] = "address_reviews"
            rec["reason"] = "Changes requested by reviewers"
        elif category == "blocked_checks":
            rec["score"] = 1
            rec["action"] = "fix_checks"
            rec["reason"] = "One or more CI checks failed"
        elif category == "blocked_conflicts":
            rec["score"] = 0
            rec["action"] = "rebase"
            rec["reason"] = "PR has merge conflicts"

        recommendations.append(rec)

    # Repo/Worktree Recommendations
    for repo in repos:
        # Check for prunable worktrees
        for worktree in repo.get("worktrees", []):
            if worktree.get("prunable"):
                recommendations.append({
                    "type": "worktree_prune",
                    "repo_path": repo["repo_path"],
                    "repo_name": repo["repo_name"],
                    "worktree_path": worktree["path"],
                    "score": 9,
                    "action": "prune_worktree",
                    "reason": f"Worktree at {worktree['path']} is stale: {worktree['prunable']}",
                })

        if repo["classification"] == "registered_worktree":
            if not repo["is_dirty"] and repo["current_branch"] == "main":
                tracking = repo["tracking"]
                if tracking["ahead"] == 0 and tracking["behind"] == 0:
                    recommendations.append({
                        "type": "worktree_cleanup",
                        "repo_path": repo["repo_path"],
                        "repo_name": repo["repo_name"],
                        "score": 8,
                        "action": "remove_worktree",
                        "reason": "Worktree is on main, sync with upstream, and not dirty",
                    })

    # Sort by score descending
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool": "nix-repo-fleet",
        "subcommand": "rank",
        "status": "ok",
        "recommendation_count": len(recommendations),
        "recommendations": recommendations,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repo-fleet")
    subparsers = parser.add_subparsers(dest="subcommand")

    repos_parser = subparsers.add_parser("repos")
    repos_parser.add_argument("--root", default=".")

    prs_parser = subparsers.add_parser("prs")
    prs_parser.add_argument("--owner")
    prs_parser.add_argument("--repo")
    prs_parser.add_argument("--state", default="open")
    prs_parser.add_argument("--limit", type=int, default=30)

    rank_parser = subparsers.add_parser("rank")
    rank_parser.add_argument("--root", default=".")
    rank_parser.add_argument("--owner")
    rank_parser.add_argument("--repo")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    subcommand = args.subcommand or "repos"

    if subcommand == "repos":
        return repos_command(args)
    if subcommand == "prs":
        return prs_command(args)
    if subcommand == "rank":
        return rank_command(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
