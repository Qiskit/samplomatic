#!/usr/bin/env python3
# This code is a Qiskit project.
#
# (C) Copyright IBM 2024, 2025.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Utility script to verify consistent spelling of certain words."""

#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
from pathlib import Path

IGNORE_PATTERN = re.compile(r"#\s*ignore-spelling\b", re.IGNORECASE)
"""Use '# ignore-spelling' skip the spelling check."""


def parse_banned_words(ban_list):
    banned = {}
    for item in ban_list:
        try:
            word, replacement = item.split("-", 1)
            banned[word.strip()] = replacement.strip()
        except ValueError:
            print(f"Invalid --ban format: '{item}'. Use word-replacement.", file=sys.stderr)
            sys.exit(2)
    return banned


def get_diff_files():
    result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True)
    return [Path(f) for f in result.stdout.strip().splitlines() if f.endswith(".py")]


def check_file(file_path, banned_words):
    violations = []
    compiled_banned_words = {re.compile(word): replace for word, replace in banned_words.items()}
    try:
        with file_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if IGNORE_PATTERN.search(line):
                    continue
                for re_pattern, replace in compiled_banned_words.items():
                    if re_pattern.search(line):
                        violations.append((file_path, i, re_pattern.pattern, replace, line.strip()))
    except Exception as e:
        print(f"Could not read {file_path}: {e}", file=sys.stderr)
    return violations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-b",
        "--ban",
        action="append",
        default=[],
        help="Banned word and replacement in the form 'word-replacement'",
    )
    args = parser.parse_args()

    all_violations = []
    for file in list(Path("samplomatic").rglob("*.py")) + list(Path("test").rglob("*.py")):
        all_violations.extend(check_file(file, parse_banned_words(args.ban)))

    if all_violations:
        for file, line, word, replacement, content in all_violations:
            msg = f"{file}:{line}: Found '{word}' — please replace with '{replacement}'"
            msg += f"\n    {content}"
            print(msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
