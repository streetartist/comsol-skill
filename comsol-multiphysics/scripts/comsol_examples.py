#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from comsol_tool import detect_installation  # noqa: E402


def examples_root(root_override: str | None) -> Path:
    installation = detect_installation(root_override)
    root = Path(installation["root"])
    return root / "applications"


def list_examples(root_override: str | None) -> list[Path]:
    app_root = examples_root(root_override)
    return sorted(app_root.rglob("*.mph"))


def score(path: Path, keywords: list[str]) -> int:
    haystack = str(path).lower()
    return sum(1 for kw in keywords if kw in haystack)


def search_command(args: argparse.Namespace) -> int:
    keywords = [kw.lower() for kw in args.keywords]
    results = []
    for path in list_examples(args.root):
        matched = score(path, keywords)
        if matched:
            results.append(
                {
                    "path": str(path),
                    "name": path.name,
                    "score": matched,
                }
            )
    results.sort(key=lambda item: (-item["score"], item["path"]))
    if args.limit:
        results = results[: args.limit]
    print(json.dumps(results, indent=2))
    return 0


def copy_command(args: argparse.Namespace) -> int:
    source = Path(args.source).resolve()
    dest = Path(args.dest).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    print(str(dest))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Search and copy COMSOL Application Library examples.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    search = subparsers.add_parser("search", help="Search local Application Library models by keyword.")
    search.add_argument("keywords", nargs="+", help="One or more search keywords.")
    search.add_argument("--limit", type=int, default=20, help="Maximum number of matches.")
    search.add_argument("--root", help="Optional COMSOL installation root override.")
    search.set_defaults(func=search_command)

    copy = subparsers.add_parser("copy", help="Copy an Application Library model to a working location.")
    copy.add_argument("--source", required=True, help="Absolute path to the source .mph file.")
    copy.add_argument("--dest", required=True, help="Destination path.")
    copy.set_defaults(func=copy_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
