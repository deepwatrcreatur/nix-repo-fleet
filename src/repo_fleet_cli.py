#!/usr/bin/env python3
import json
import sys


def main() -> int:
    argv = sys.argv[1:]
    subcommand = argv[0] if argv else "repos"
    payload = {
        "schema_version": 1,
        "tool": "nix-repo-fleet",
        "subcommand": subcommand,
        "status": "placeholder",
        "message": "CLI contract scaffold only; implementation pending",
        "supported_subcommands": ["repos", "prs", "rank"],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
