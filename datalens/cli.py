"""Command-line interface for DataLens."""

from __future__ import annotations

import argparse
import sys

from datalens import inspect_file


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Inspect structured data files.")
    parser.add_argument("path", help="Path to the input file")
    parser.add_argument("--depth", type=int, default=4, help="Maximum recursion depth")
    parser.add_argument("--items", type=int, default=5, help="Maximum displayed items per container")
    parser.add_argument(
        "--format",
        default="tree",
        choices=["tree", "json", "md", "markdown"],
        help="Output format",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = inspect_file(
            args.path,
            max_depth=args.depth,
            max_items=args.items,
            format=args.format,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

