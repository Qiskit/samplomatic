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

"""Errors"""


class BuildError(Exception):
    """Error raised when building a circuit template and samplex pair."""


class ParameterError(Exception):
    """Error raised when supplying or evaluating parameters."""


class SamplexBuildError(BuildError):
    """Error raised when building a samplex."""


class SamplexError(Exception):
    """Error raised when sampling in a samplex."""


class SamplexConstructionError(SamplexError):
    """A samplex error raised during samplex finalization and validation."""


class SamplexInputError(SamplexError):
    """A samplex error raised for invalid input."""


class SamplexRuntimeError(SamplexError):
    """A samplex error raised during sampling."""


class SynthError(Exception):
    """Error raised when there is a synthesis problem."""


class TemplateBuildError(BuildError):
    """Error raised when building a template circuit."""


class VirtualGateError(Exception):
    """Error raised when there is a problem interacting with virtual gates."""


class DeserializationError(Exception):
    """Error raised when there is a problem during deserialization."""
