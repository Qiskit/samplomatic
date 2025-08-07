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

"""Optionals"""

from qiskit.utils import LazyImportTester, LazySubprocessTester

HAS_PLOTLY = LazyImportTester("plotly")

HAS_NBFORMAT = LazyImportTester("nbformat")

HAS_GRAPHVIZ = LazySubprocessTester(
    ("dot", "-V"),
    name="Graphviz",
    msg=(
        "To install, follow the OS-dependent instructions at https://graphviz.org/download/. "
        "This is not a pip-installable dependency."
    ),
)
