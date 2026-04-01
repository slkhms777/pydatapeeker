"""Command-line interface for PyDataPeekr."""

from __future__ import annotations

import argparse
import sys

from pydatapeekr import inspect_file


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Inspect structured data files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("path", help="Path to the input file")
    parser.add_argument("--max-depth", type=int, default=4, help="Maximum recursion depth")
    parser.add_argument(
        "--max-dict-items",
        type=int,
        default=8,
        help="Maximum displayed entries for dict-like nodes",
    )
    parser.add_argument(
        "--max-list-items",
        type=int,
        default=1,
        help="Maximum displayed entries for list-like nodes",
    )
    parser.add_argument("--show-sample", action="store_true", help="Show sample values for basic leaf types")
    parser.add_argument(
        "--format",
        default="tree",
        choices=["tree", "markdown"],
        help="Output format",
    )
    parser.add_argument(
        "--write-to-file",
        nargs="?",
        const=True,
        default=None,
        metavar="OUTPUT_PATH",
        help='Write output to a file. Default name: "data_info_{file_name}.txt". Supported suffixes: .txt, .md, .markdown',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        output = inspect_file(
            args.path,
            max_depth=args.max_depth,
            max_dict_items=args.max_dict_items,
            max_list_items=args.max_list_items,
            show_sample=args.show_sample,
            format=args.format,
            write_to_file=args.write_to_file,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
