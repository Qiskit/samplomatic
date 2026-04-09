# This code is a Qiskit project.
#
# (C) Copyright IBM 2025-2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Utility functions."""

from .box_key import BoxKey
from .deprecation import deprecate_arg
from .find_unique_box_instructions import find_unique_box_instructions
from .frozen_dict import FrozenDict
from .get_annotation import get_annotation
from .map_annotations import (
    extend_annotations,
    filter_annotations,
    map_annotations,
    replace_annotations,
    strip_annotations,
)
from .unbox import unbox
from .undress_box import undress_box
from .validate_literals import validate_literals
