from __future__ import annotations

import argparse
import json
import sys
import tokenize
from pathlib import Path

from . import __version__
from .core import find_duplicates


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Find duplicated token blocks in Python source.")
    value.add_argument("filters", nargs="*", help="Only analyze paths that contain one of these fragments.")
    value.add_argument("--root", type=Path, default=Path("."), help="Project root.")
    value.add_argument("--min-tokens", type=int, default=30, help="Minimum normalized token count.")
    value.add_argument("--max-groups", type=int, default=50, help="Maximum groups to report.")
    value.add_argument("--json", action="store_true", dest="json_output", help="Write JSON output.")
    value.add_argument("--fail", action="store_true", help="Exit with status 2 when duplication is found.")
    value.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        duplicates = find_duplicates(args.root.resolve(), args.min_tokens, args.filters, args.max_groups)
    except (OSError, ValueError, tokenize.TokenError) as error:  # type: ignore[name-defined]
        print(f"dry4python: {error}", file=sys.stderr)
        return 1
    if args.json_output:
        print(json.dumps([duplicate.to_dict() for duplicate in duplicates], indent=2, sort_keys=True))
    elif not duplicates:
        print("No duplicated blocks found.")
    else:
        print("DRY Report\n==========")
        for index, duplicate in enumerate(duplicates, 1):
            print(f"\nGroup {index}: {duplicate.token_count} normalized tokens")
            for location in duplicate.locations:
                print(f"  {location.file}:{location.start_line}-{location.end_line}")
    return 2 if args.fail and duplicates else 0
