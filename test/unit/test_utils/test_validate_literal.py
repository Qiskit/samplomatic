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

"""Tests for ``validate_literal``"""

from typing import Literal

import pytest

from samplomatic.utils import validate_literals


def test_valid_values():
    """Test valid values pass."""

    @validate_literals("color", "shape")
    def draw(color: Literal["red", "green"], shape: Literal["circle", "square"]) -> str:
        return f"{color} {shape}"

    assert draw("red", "circle") == "red circle"


def test_invalid_color():
    """Test invalid color raises."""

    @validate_literals("color", "shape")
    def draw(color: Literal["red", "green"], shape: Literal["circle", "square"]) -> str:
        return f"{color} {shape}"

    with pytest.raises(ValueError, match="Invalid value for argument 'color'"):
        draw("blue", "circle")


def test_invalid_shape():
    """Test invalid shape raises."""

    @validate_literals("color", "shape")
    def draw(color: Literal["red", "green"], shape: Literal["circle", "square"]) -> str:
        return f"{color} {shape}"

    with pytest.raises(ValueError, match="Invalid value for argument 'shape'"):
        draw("red", "triangle")


def test_missing_argument_in_function():
    """Test missing argument raises at decorator creation."""
    with pytest.raises(ValueError, match="has no argument named 'shade'"):

        @validate_literals("shade")
        def draw(color: str) -> str:
            return color


def test_missing_argument_annotation_in_function():
    """Test missing argument annotation raises at decorator creation."""
    with pytest.raises(TypeError, match="Argument 'color' has no type annotation."):

        @validate_literals("color")
        def draw(color) -> str:
            return color


def test_with_default_arguments():
    """Test default arguments validated correctly."""

    @validate_literals("color", "shape")
    def draw(color: Literal["red", "green"], shape: Literal["circle", "square"] = "square") -> str:
        return f"{color} {shape}"

    assert draw("green") == "green square"
