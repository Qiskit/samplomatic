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

"""Utility script to verify copyright file headers."""

import argparse
import re
import sys
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# regex for character encoding from PEP 263
pep263 = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)")
allow_path = re.compile(r"^[-_a-zA-Z0-9]+")

HEADER = """# This code is a Qiskit project.
#
# (C) Copyright IBM 2025.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals."""


def discover_files(
    roots: Iterable[str],
    extensions: set[str] = frozenset({".py", ".pyx", ".pxd"}),
    omit: str = "",
) -> Iterable[str]:
    """Find all .py, .pyx, .pxd files in a list of trees."""
    for code_path in roots:
        path = Path(code_path)
        if path.is_dir():
            # Recursively search for files with the specified extensions
            for file in path.rglob("*"):
                if file.suffix in extensions and not file.match(omit):
                    yield str(file)


def validate_header(file_path: str) -> tuple[str, bool, str]:
    """Validate the header for a single file."""
    with open(file_path, encoding="utf8") as fd:
        lines = fd.readlines()
    start = 0
    for index, line in enumerate(lines):
        if index > 5:
            return file_path, False, "Header not found in first 5 lines"
        if index <= 2 and pep263.match(line):
            return (
                file_path,
                False,
                "Unnecessary encoding specification (PEP 263, 3120)",
            )
        if line.strip().startswith(HEADER.split("\n", maxsplit=1)[0]):
            start = index
            break

    for idx, (actual, required) in enumerate(zip(lines[start:], HEADER.split("\n"))):
        if idx == 2:
            if not actual.startswith("# (C) Copyright IBM 20"):
                return (file_path, False, "Header copyright year line not found or invalid")
        elif (actual := actual.strip()) != (required := required.strip()):
            return (
                file_path,
                False,
                f"Header line {1 + start + idx} '{actual}' does not match '{required}'.",
            )
    return file_path, True, None


def main():
    try:
        """Run verification."""
        default_path = Path(__file__).resolve().parent.parent / "samplomatic"

        parser = argparse.ArgumentParser(description="Check file headers.")
        parser.add_argument(
            "paths",
            type=Path,
            nargs="*",
            default=[default_path],
            help="Paths to scan; defaults to '../samplomatic' relative to the script location.",
        )
        parser.add_argument(
            "-o",
            "--omit",
            type=str,
            default="",
            help="Glob of files to omit.",
        )
        args = parser.parse_args()

        python_files = discover_files(map(str, args.paths), omit=args.omit)
        with ProcessPoolExecutor() as executor:
            results = executor.map(validate_header, python_files)

        failed_files = [(file_path, err) for file_path, success, err in results if not success]
        if failed_files:
            for file_path, error_message in failed_files:
                sys.stderr.write(f"{file_path} failed header check because:\n")
                sys.stderr.write(f"{error_message}\n\n")
            sys.exit(1)

        sys.exit(0)
    except Exception as exc:
        print(exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
