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

"""ParameterExpressionTable Serializers"""

import io

import pybase64
from qiskit import QuantumCircuit
from qiskit.qpy import dump, load

from ..samplex.parameter_expression_table import ParameterExpressionTable
from .type_serializer import DataSerializer, TypeSerializer


class ParameterExpressionTableSerializer(TypeSerializer[ParameterExpressionTable]):
    """Serializer for :class:`~.ParameterExpressionTable`."""

    TYPE_ID = "P"
    TYPE = ParameterExpressionTable

    class SSV1(DataSerializer[ParameterExpressionTable]):
        MIN_SSV = 1

        @classmethod
        def serialize(cls, obj):
            # qiskit doesn't have a direct way to serialize a list of parameter expressions. in
            # stick to the public qpy interface, the simplest solution is to put them inside of an
            # object that qpy can serialize.
            circuit = QuantumCircuit(1)
            for expr in obj._expressions:  # noqa: SLF001
                circuit.rz(expr, 0)

            with io.BytesIO() as buf:
                dump(circuit, buf, version=15)
                circuit_base64 = pybase64.b64encode_as_string(buf.getvalue())

            return {"qpy": "15", "circuit_base64": circuit_base64}

        @classmethod
        def deserialize(cls, data):
            with io.BytesIO(pybase64.b64decode(data["circuit_base64"])) as buf:
                circuit = load(buf)[0]

            param_table = ParameterExpressionTable()
            for instr in circuit:
                param_table.append(instr.operation.params[0])
            return param_table
