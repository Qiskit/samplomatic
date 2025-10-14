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

"""ParameterExpressionTable"""

import numpy as np
from qiskit.circuit import ParameterVectorElement

from ..aliases import Parameter, ParameterExpression, ParamIndex, ParamName, ParamValues
from ..exceptions import ParameterError


def _sort_key(parameter: Parameter):
    if isinstance(parameter, ParameterVectorElement):
        return (parameter.vector.name, parameter.index)
    return (parameter.name,)


class ParameterExpressionTable:
    r"""Evaluates a list of parameter expressions given a list of parameter values.

    An instance of this class owns an ordered list of :math:`M` :class:`ParameterExpression`\s
    that together implicitly specify an ordered list of distinct :math:`N` :class:`Parameter`\s.
    Because parameter expressions can involve multiple parameters, because distinct parameter
    expressions can reference the same parameters, and because parameter expressions that are
    completely bound contain no parameters, there is in general no relationship between
    :math:`N` and :math:`M`. However, :math:`N=M` in the common special case that all parameter
    expressions are just, in fact, unique parameters.

    The :meth:`~evaluate` method accepts :math:`N` parameter values, and returns numeric
    values for each of the :math:`M` parameter expressions.

    This class can be used as a shim for tools that want to accept parameter values but use
    expressions of them without the tedious responsibilities usually attached.
    """

    def __init__(self):
        self._expressions: list[ParameterExpression] = []
        self._parameters: dict[ParamName, Parameter] = {}
        self._sorted = True

    def append(self, expression: ParameterExpression) -> ParamIndex:
        r"""Add a parameter expression to the table.

        Args:
            expression: The parameter expression to append.

        Returns:
            The index of the appended expression.

        Raises:
            ParameterError: If the expression contains a parameter that is not already in this table
                but whose name conflicts with an existing parameter. Keep in mind that
                :class:`Parameter`\s use instance equality.
        """
        for parameter in expression.parameters:
            if self._parameters.get(name := parameter.name) not in (None, parameter):
                for parameter in expression.parameters:
                    # avoid side effects by popping what may have already been added
                    self._parameters.pop(parameter.name, None)
                raise ParameterError(f"A parameter with name '{name}' already exists.")
            self._parameters[name] = parameter

        self._expressions.append(expression)
        self._sorted = False
        return len(self._expressions) - 1

    @property
    def parameters(self) -> list[Parameter]:
        """The unique parameters across all expressions in sorted order.

        The same sorting order as qiskit is used, where :class:`ParameterVector` elements are
        arranged numerically, but otherwise alphabetically by name.
        """
        if not self._sorted:
            sorted_parameters = sorted(self._parameters.values(), key=_sort_key)
            self._parameters = {parameter.name: parameter for parameter in sorted_parameters}
        return list(self._parameters.values())

    @property
    def num_parameters(self) -> int:
        """The number of unique input parameters across all expressions."""
        return len(self._parameters)

    @property
    def num_expressions(self) -> int:
        """The number of parameter expressions to evaluate; the return size of :meth:`~evaluate`."""
        return len(self._expressions)

    def evaluate(self, parameter_values: ParamValues) -> np.ndarray:
        r"""Return one numeric value for each expression.

        Args:
            parameter_values: The parameter values, either as a map from parameters to their values,
                or just the values in parameter-sorted order (see :attr:`~parameters`\).

        Returns:
            An array of evaluated expressions.

        Raises:
            ParameterError: If the correct number of parameters is not supplied, or if some
                expression requires a value for a parameter that was not provided.
        """
        if len(parameter_values) != self.num_parameters:
            raise ParameterError(
                f"Expecting {self.num_parameters} parameters but received {len(parameter_values)}."
            )

        if not isinstance(parameter_values, dict):
            parameter_values = dict(zip(self.parameters, parameter_values))

        try:
            return np.array(
                [expression.bind_all(parameter_values) for expression in self._expressions],
                dtype=float,
            )
        except KeyError as exc:
            raise ParameterError(f"Missing value for {exc}.")
