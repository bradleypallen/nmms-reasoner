"""CLI entry point for pyNMMS.

Usage::

    pynmms tell -b base.json --create "A |~ B"
    pynmms tell -b base.json --create --rq "Happy(alice) |~ Good(alice)"
    pynmms ask  -b base.json "A => B"
    pynmms ask  -b base.json --rq "ALL hasChild.Happy(alice), hasChild(alice,bob) => Happy(bob)"
    pynmms repl [-b base.json] [--rq]
"""

from __future__ import annotations

import argparse
import sys

from pynmms._version import __version__


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the ``pynmms`` CLI."""
    parser = argparse.ArgumentParser(
        prog="pynmms",
        description="pyNMMS — Non-Monotonic Multi-Succedent sequent calculus",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- tell ---
    tell_parser = subparsers.add_parser("tell", help="Add atoms or consequences to a base")
    tell_parser.add_argument("-b", "--base", required=True, help="Path to JSON base file")
    tell_parser.add_argument(
        "--create", action="store_true", help="Create the base file if missing",
    )
    tell_parser.add_argument(
        "statement", nargs="?", default=None,
        help='Statement: "A |~ B" or "atom A" (use - for stdin)',
    )
    tell_parser.add_argument(
        "--rq", action="store_true",
        help="Use restricted quantifier mode (concept/role assertions)",
    )
    tell_output = tell_parser.add_mutually_exclusive_group()
    tell_output.add_argument(
        "--json", action="store_true", help="Output as JSON (pipe-friendly)",
    )
    tell_output.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress output; rely on exit code",
    )
    tell_parser.add_argument(
        "--batch", metavar="FILE",
        help="Read statements from FILE (use - for stdin), one per line",
    )

    # --- ask ---
    ask_parser = subparsers.add_parser("ask", help="Query derivability of a sequent")
    ask_parser.add_argument("-b", "--base", required=True, help="Path to JSON base file")
    ask_parser.add_argument("--trace", action="store_true", help="Print proof trace")
    ask_parser.add_argument(
        "--max-depth", type=int, default=25, help="Max proof depth (default: 25)",
    )
    ask_parser.add_argument(
        "sequent", nargs="?", default=None,
        help='Sequent: "A => B" or "A, B => C, D" (use - for stdin)',
    )
    ask_parser.add_argument(
        "--rq", action="store_true",
        help="Use restricted quantifier mode",
    )
    ask_output = ask_parser.add_mutually_exclusive_group()
    ask_output.add_argument(
        "--json", action="store_true", help="Output as JSON (pipe-friendly)",
    )
    ask_output.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress output; rely on exit code",
    )
    ask_parser.add_argument(
        "--batch", metavar="FILE",
        help="Read sequents from FILE (use - for stdin), one per line",
    )

    # --- repl ---
    repl_parser = subparsers.add_parser("repl", help="Interactive REPL")
    repl_parser.add_argument("-b", "--base", default=None, help="Path to JSON base file to load")
    repl_parser.add_argument(
        "--rq", action="store_true",
        help="Use restricted quantifier mode",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "tell":
        from pynmms.cli.tell import run_tell
        return run_tell(args)
    elif args.command == "ask":
        from pynmms.cli.ask import run_ask
        return run_ask(args)
    elif args.command == "repl":
        from pynmms.cli.repl import run_repl
        return run_repl(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
