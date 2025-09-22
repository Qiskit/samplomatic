# This code is a Qiskit project.
#
# (C) Copyright IBM 2025.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import re
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("filename", ["README.md", "DEPRECATION.md"])
def test_markdown_codeblocks(tmp_path, filename):
    """Test python snippets in base-level markdown files."""
    readme = Path(__file__).parent.parent.parent / filename
    text = readme.read_text()

    # Extract fenced code blocks
    blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    if not blocks:
        raise AssertionError(f"No python code blocks found in {filename}")

    merged_code = "\n\n".join(blocks)

    # Write merged code to a temp file
    script = tmp_path / f"{filename.split('.')[0]}_examples.py"
    script.write_text(merged_code)

    # Run it as a subprocess
    proc = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        raise AssertionError(
            f"README example failed (see {script}):\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
