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

"""U2ParametricMultiplicationNode"""

from typing import Literal

import numpy as np
import orjson

from ...aliases import ParamIndex, RegisterName, Self, SubsystemIndex
from ...annotations import VirtualType
from ...exceptions import SamplexConstructionError, SamplexRuntimeError
from ...virtual_registers import U2Register, VirtualRegister
from .evaluation_node import EvaluationNode


class U2ParametricMultiplicationNode(EvaluationNode):
    """Abstract parent node for nodes doing multiplication on a :class:`~.U2Register`.

    The node stores a parametric representation of a one-qubit gate or gates from the
    original circuit to perform multiplication on a registry.

    Limited to the gates ``rz`` or ``rx``, and all gates within the node are of the
    same type.

    Args:
        operand: The gate type, given as a string.
        register_name: The name of the register the operation is applied to.
        param_idxs: List of ``ParamIndex`` for the parameter expressions specifying the gate
            arguments. List order must match the order subsystems in the registry.

    Raises:
        SamplexConstructionError: if `param_idxs` is empty.
        SamplexConstructionError: if `operand` is not ``rz`` or ``rx``.
    """

    def __init__(
        self,
        operand: Literal["rz", "rx"],
        register_name: RegisterName,
        param_idxs: list[ParamIndex],
    ):
        if not param_idxs:
            raise SamplexConstructionError("Expected at least one element in param_idxs")

        if operand not in {"rz", "rx"}:
            raise SamplexConstructionError(f"Unexpected operand {operand}")

        self._operand = operand
        self._param_idxs = param_idxs
        self._register_name = register_name

    @classmethod
    def _from_json_dict(cls, data: dict[str, str]) -> Self:
        return cls(
            data["operand"],
            data["register_name"],
            orjson.loads(data["param_indices"]),
        )

    def get_style(self):
        return (
            super()
            .get_style()
            .append_data("Operand", repr(self._operand))
            .append_data("Parameter Indices", repr(self._param_idxs))
        )

    @property
    def parameter_idxs(self) -> list[ParamIndex]:
        """Which evaluated parameter expressions this node needs access to at sampling time."""
        return self._param_idxs

    @property
    def outgoing_register_type(self) -> VirtualType:
        return VirtualType.U2

    def writes_to(self) -> dict[RegisterName, tuple[set[SubsystemIndex], type[VirtualType]]]:
        return {self._register_name: (set(range(self.num_parameters)), VirtualType.U2)}

    def _get_operation(self, parameter_values: np.ndarray) -> U2Register:
        """Generate the U2Register for the evaluated operation"""
        result = np.empty((len(parameter_values), 1, 2, 2), dtype=U2Register.DTYPE)

        if self._operand == "rx":
            result[:, 0, 0, 0] = np.cos(0.5 * parameter_values)
            result[:, 0, 0, 1] = -1j * np.sin(0.5 * parameter_values)
            result[:, 0, 1, 0] = result[:, 0, 0, 1]
            result[:, 0, 1, 1] = result[:, 0, 0, 0]
        else:
            result[:, 0, 0, 0] = np.exp(-0.5j * parameter_values)
            result[:, 0, 0, 1] = 0
            result[:, 0, 1, 0] = 0
            result[:, 0, 1, 1] = np.exp(0.5j * parameter_values)

        return U2Register(result)


class LeftU2ParametricMultiplicationNode(U2ParametricMultiplicationNode):
    """Perform parametric left multiplication on a :class:`~.U2Register`.

    The node stores a parametric representation :math:`g` of a one-qubit gate or gates from the
    original circuit and performs a :math:`g*reg` multiplication, where :math:`reg` is the existing
    ``U2Register``.

    :math:`g` is limited to the gates ``rz`` or ``rx``, and all gates within the node are of the
    same type:math:.

    Args:
        operand: The gate type, given as a string.
        register_name: The name of the register the operation is applied to.
        param_idxs: List of ``ParamIndex`` for the parameter expressions specifying the gate
            arguments. List order must match the order subsystems in the register.

    Raises:
        SamplexConstructionError: if `param_idxs` is empty.
    """

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "10",
            "operand": self._operand,
            "param_indices": orjson.dumps(self._param_idxs).decode("utf-8"),
            "register_name": self._register_name,
        }

    def evaluate(
        self, registers: dict[RegisterName, VirtualRegister], parameter_values: np.ndarray
    ):
        """Evaluate this node.

        Args:
            registers: At least those registers needed by this node to read from or write to.
            parameter_values: The evaluated values of the parameter expressions in indices
                ``self.parameter_idxs``, at the same order.

        Raises:
            SamplexRuntimeError: If the number of parameter values doesn't match the number of
                parameter expressions in ``self.parameter_idxs``.
        """
        if len(parameter_values) != self.num_parameters:
            raise SamplexRuntimeError(
                f"Expected {self.num_parameters} parameter values instead got "
                f"{len(parameter_values)}"
            )

        registers[self._register_name].left_inplace_multiply(self._get_operation(parameter_values))


class RightU2ParametricMultiplicationNode(U2ParametricMultiplicationNode):
    """Perform parametric right multiplication on a :class:`~.U2Register`.

    The node stores a parametric representation :math:`g` of a one-qubit gate or gates from the
    original circuit and performs a :math:`reg*g` multiplication, where :math:`reg` is the existing
    ``U2Register``.

    :math:`g` is limited to the gates ``rz`` or ``rx``, and all gates within the node are of the
    same type.

    Args:
        operand: The gate type, given as a string.
        register_name: The name of the register the operation is applied to.
        param_idxs: List of ``ParamIndex`` for the parameter expressions specifying the gate
            arguments. List order must match the order subsystems in the registry.

    Raises:
        SamplexConstructionError: if `param_idxs` is empty.
    """

    def _to_json_dict(self) -> dict[str, str]:
        return {
            "node_type": "12",
            "operand": self._operand,
            "param_indices": orjson.dumps(self._param_idxs).decode("utf-8"),
            "register_name": self._register_name,
        }

    def evaluate(
        self, registers: dict[RegisterName, VirtualRegister], parameter_values: np.ndarray
    ):
        """Evaluate this node.

        Args:
            registers: At least those registers needed by this node to read from or write to.
            parameter_values: The evaluated values of the parameter expressions in indices
                ``self.parameter_idxs``, at the same order.

        Raises:
            SamplexRuntimeError: If the number of parameter values doesn't match the number of
                parameter expressions in ``self.parameter_idxs``.
        """
        if len(parameter_values) != self.num_parameters:
            raise SamplexRuntimeError(
                f"Expected {self.num_parameters} parameter values instead got "
                f"{len(parameter_values)}"
            )

        registers[self._register_name].inplace_multiply(self._get_operation(parameter_values))
