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
from pathlib import Path

import pytest


@pytest.mark.parametrize("filename", ["README.md", "DEPRECATION.md"])
def test_markdown_codeblocks(run_snippet, filename):
    """Test python snippets in base-level markdown files."""
    markdown_text = (Path(__file__).parent.parent.parent / filename).read_text()

    # extract fenced code blocks
    blocks = re.findall(r"```python\n(.*?)```", markdown_text, re.DOTALL)
    if not blocks:
        raise AssertionError(f"No python code blocks found in {filename}")

    run_snippet(filename.split(".")[0], "\n\n".join(blocks))
