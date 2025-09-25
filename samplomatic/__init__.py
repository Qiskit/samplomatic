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

"""Samplomatic"""

from ._beta_warning import warn_once_per_version as _warn_once_per_version
from ._version import __version__
from .annotations import BasisTransform, InjectNoise, Twirl
from .builders import build

_warn_once_per_version(
    f"\nYou have imported samplomatic=={__version__} which is in \n"
    "beta development. Please expect breaking changes between \n"
    "minor versions and pin your dependencies accordingly.",
    version_str=__version__,
    suppress_for_devs=True,
)
