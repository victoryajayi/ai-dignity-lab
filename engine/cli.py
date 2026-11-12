"""
cli.py: check a text file from the terminal and print the flags.

Usage, from the repo folder:
    python -m engine.cli corpus/demo_job_posting.txt
    python -m engine.cli corpus/demo_job_posting.txt --type hiring
"""

import argparse
import sys
import textwrap
from collections import Counter
from pathlib import Path

from engine.loader import RuleError, load_rules
from engine.matchers import check_text

CONTENT_TYPES = ["hiring", "decisions", "education", "customer_service", "communications"]


def print_flag(number, flag):
    """Print one flag as a small, readable Rule Card."""
    wrap = lambda text: textwrap.fill(text, width=78, initial_indent="     ",
                                      subsequent_indent="     ")
    print(f"{number}. [{flag.severity.upper()}] {flag.rule_id}  "
          f"{flag.lens.title()} / {flag.category}")
    print(f'   Matched: "{flag.matched_text}"')
    print(f"   In:")
    print(wrap(f'"{flag.sentence}"'))
    print(f"   Why:")
    print(wrap(flag.why))
    print(f"   Affects: {flag.who_is_affected}")
    print(f"   Try:")
    print(wrap(flag.suggestion))
    if flag.limitations:
        print(f"   Human check:")
        print(wrap(flag.limitations))
    print(f"   Source: {flag.source_title}")
    print(f"           {flag.source_url}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Check a text file with AI Dignity Lab rules.")
    parser.add_argument("file", help="path to a .txt file to check")
    parser.add_argument("--type", choices=CONTENT_TYPES, default=None,
                        help="content type; only rules that apply to it will run")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        sys.exit(f"File not found: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        sys.exit(f"{path.name} is empty. Add some text and try again.")

    try:
        rules = load_rules()
    except RuleError as err:
        sys.exit(f"Rule problem: {err}")

    flags = check_text(text, rules, content_type=args.type)

    type_note = f" (content type: {args.type})" if args.type else " (all content types)"
    print(f"\nAI Dignity Lab: {len(rules)} rules loaded{type_note}")
    print(f"Checked: {path.name}\n")

    if not flags:
        print("No flags found. A person should still review the text.\n")
        return

    for number, flag in enumerate(flags, start=1):
        print_flag(number, flag)

    by_severity = Counter(flag.severity for flag in flags)
    by_lens = Counter(flag.lens for flag in flags)
    print(f"Total: {len(flags)} flags  |  "
          f"High {by_severity['high']}, Medium {by_severity['medium']}, Low {by_severity['low']}  |  "
          f"Fairness {by_lens['fairness']}, Respect {by_lens['respect']}, Access {by_lens['access']}")
    print("This is a screening tool. A person makes the final call.\n")


if __name__ == "__main__":
    main()
