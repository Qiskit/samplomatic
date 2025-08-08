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

import numpy as np
import pytest
from scipy.linalg import expm

from samplomatic.annotations import VirtualType
from samplomatic.distributions import HaarU2
from samplomatic.exceptions import SamplexConstructionError, SamplexRuntimeError
from samplomatic.samplex.nodes import (
    LeftU2ParametricMultiplicationNode,
    RightU2ParametricMultiplicationNode,
)

X_MATRIX = np.array([[0, 1], [1, 0]])
Z_MATRIX = np.array([[1, 0], [0, -1]])


class TestLeftU2ParamMultiplicationNode:
    def test_instantiation_errors(self):
        """Test that errors are properly raised during instantiation"""
        with pytest.raises(
            SamplexConstructionError,
            match="Expected at least one element in param_idxs",
        ):
            LeftU2ParametricMultiplicationNode("rz", "a", [])

        with pytest.raises(
            SamplexConstructionError,
            match="Unexpected operand",
        ):
            LeftU2ParametricMultiplicationNode("rzz", "a", [0])

    def test_evaluation_errors(self):
        """Test that errors are properly raised during evaluation"""
        node = LeftU2ParametricMultiplicationNode("rz", "a", [0, 1, 2])
        registers = {}
        with pytest.raises(
            SamplexRuntimeError, match=re.escape("Expected 3 parameter values instead got 1")
        ):
            node.evaluate(registers, [1])

    @pytest.mark.parametrize("gate,matrix", [("rx", X_MATRIX), ("rz", Z_MATRIX)])
    def test_left_multiply(self, gate, matrix, rng):
        """Test left multiply"""
        register_shape = [5, 2]

        params = rng.random(register_shape[0]) * 2 * np.pi
        haar_dist = HaarU2(register_shape[0])
        node = LeftU2ParametricMultiplicationNode(gate, "a", [i for i in range(register_shape[0])])
        assert node.outgoing_register_type is VirtualType.U2
        register = haar_dist.sample(register_shape[1], rng)
        registers = {"a": register.copy()}
        node.evaluate(registers, params)

        operation = expm(
            -0.5j
            * np.tile(matrix, (register_shape[0], 1, 1, 1))
            * params.reshape((len(params), 1, 1, 1))
        )
        assert np.allclose(
            registers["a"].virtual_gates, np.matmul(operation, register.virtual_gates)
        )


class TestRightU2ParamMultiplicationNode:
    def test_instantiation_errors(self):
        """Test that errors are properly raised during instantiation"""
        with pytest.raises(
            SamplexConstructionError,
            match="Expected at least one element in param_idxs",
        ):
            RightU2ParametricMultiplicationNode("rz", "a", [])

    def test_evaluation_errors(self):
        """Test that errors are properly raised during evaluation"""
        node = RightU2ParametricMultiplicationNode("rz", "a", [0, 1, 2])
        registers = {}
        with pytest.raises(
            SamplexRuntimeError, match=re.escape("Expected 3 parameter values instead got 1")
        ):
            node.evaluate(registers, [1])

    @pytest.mark.parametrize("gate,matrix", [("rx", X_MATRIX), ("rz", Z_MATRIX)])
    def test_left_multiply(self, gate, matrix, rng):
        """Test left multiply"""
        register_shape = [5, 2]

        params = rng.random(register_shape[0]) * 2 * np.pi
        haar_dist = HaarU2(register_shape[0])
        node = RightU2ParametricMultiplicationNode(gate, "a", [i for i in range(register_shape[0])])
        register = haar_dist.sample(register_shape[1], rng)
        registers = {"a": register.copy()}
        node.evaluate(registers, params)

        operation = expm(
            -0.5j
            * np.tile(matrix, (register_shape[0], 1, 1, 1))
            * params.reshape((len(params), 1, 1, 1))
        )
        assert np.allclose(
            registers["a"].virtual_gates, np.matmul(register.virtual_gates, operation)
        )
