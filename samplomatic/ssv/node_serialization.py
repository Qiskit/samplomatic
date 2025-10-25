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

"""Node Serialization"""

import orjson

from ..annotations import VirtualType
from ..distributions import HaarU2, UniformPauli
from ..exceptions import DeserializationError
from ..samplex.nodes import (
    ChangeBasisNode,
    CollectTemplateValues,
    CollectZ2ToOutputNode,
    CombineRegistersNode,
    ConversionNode,
    InjectNoiseNode,
    LeftMultiplicationNode,
    LeftU2ParametricMultiplicationNode,
    PauliPastCliffordNode,
    RightMultiplicationNode,
    RightU2ParametricMultiplicationNode,
    SliceRegisterNode,
    TwirlSamplingNode,
)
from ..samplex.nodes.change_basis_node import BasisChange
from ..samplex.nodes.combine_registers_node import CombineType
from ..synths import RzRxSynth, RzSxSynth
from ..virtual_registers.serialization import virtual_register_from_json
from .type_serializer import DataSerializer, TypeSerializer
from .utils import array_from_str, array_to_str, slice_from_json, slice_to_json


class ChangeBasisNodeSerializer(TypeSerializer[ChangeBasisNode]):
    """Serializer for :class:`~.ChangeBasisNode`."""

    TYPE_ID = "0"

    class TSV1(DataSerializer[ChangeBasisNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "register_name": obj._register_name,  # noqa: SLF001
                "basis_change": orjson.dumps(obj._basis_change.to_json_dict()).decode("utf-8"),  # noqa: SLF001
                "basis_ref": obj._basis_ref,  # noqa: SLF001
                "num_subsystems": str(obj._num_subsystems),  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            return ChangeBasisNode(
                data["register_name"],
                BasisChange.from_json_dict(orjson.loads(data["basis_change"])),
                data["basis_ref"],
                int(data["num_subsystems"]),
            )


class CollectTemplateValuesSerializer(TypeSerializer[CollectTemplateValues]):
    """Serializer for :class:`~.CollectTemplateValues`."""

    TYPE_ID = "1"

    class TSV1(DataSerializer[CollectTemplateValues]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "template_param_names": obj._template_params_name,  # noqa: SLF001
                "template_idxs": array_to_str(obj._template_idxs),  # noqa: SLF001
                "register_type": obj._register_type,  # noqa: SLF001
                "register_name": obj._register_name,  # noqa: SLF001
                "subsystem_idxs": array_to_str(obj._subsystem_idxs),  # noqa: SLF001
                "synth": type(obj._synth).__name__,  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            synth_class_name = data["synth"]
            if synth_class_name == "RzRxSynth":
                synth = RzRxSynth()
            elif synth_class_name == "RzSxSynth":
                synth = RzSxSynth()
            else:
                raise DeserializationError(f"Invalid Synth class: {synth_class_name}")

            return CollectTemplateValues(
                data["template_param_names"],
                array_from_str(data["template_idxs"]),
                data["register_name"],
                VirtualType(data["register_type"]),
                array_from_str(data["subsystem_idxs"]),
                synth,
            )


class CollectZ2ToOutputNodeSerializer(TypeSerializer[CollectZ2ToOutputNode]):
    """Serializer for :class:`~.CollectZ2ToOutputNode`."""

    TYPE_ID = "2"

    class TSV1(DataSerializer[CollectZ2ToOutputNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            {
                "register_name": obj._register_name,  # noqa: SLF001
                "output_name": obj._output_name,  # noqa: SLF001
                "subsystem_indices": array_to_str(obj._subsystem_idxs),  # noqa: SLF001
                "output_indices": array_to_str(obj._output_idxs),  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            return CollectZ2ToOutputNode(
                data["register_name"],
                array_from_str(data["subsystem_indices"]),
                data["output_name"],
                array_from_str(data["output_indices"]),
            )


class CombineRegistersNodeSerializer(TypeSerializer[CombineRegistersNode]):
    """Serializer for :class:`~.CombineRegistersNode`."""

    TYPE_ID = "3"

    class TSV1(DataSerializer[CombineRegistersNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            operands_dict = {}
            for key, values in obj._operands.items():  # noqa: SLF001
                value_list = []
                for v in values:
                    if isinstance(v, VirtualType):
                        value_list.append({"type": v.value})
                    elif isinstance(v, CombineType):
                        continue
                    else:
                        value_list.append({"array": array_to_str(v)})
                operands_dict[key] = value_list

            return {
                "output_type": obj._output_type.value,  # noqa: SLF001
                "output_register_name": obj._output_register_name,  # noqa: SLF001
                "num_output_subsystems": str(obj._num_output_subsystems),  # noqa: SLF001
                "operands": orjson.dumps(operands_dict).decode("utf-8"),
            }

        @classmethod
        def deserialize(cls, data):
            raw_operands_dict = orjson.loads(data["operands"])
            operands = {}
            for name, values in raw_operands_dict.items():
                tuple_value = []
                for value in values:
                    if array_str := value.get("array"):
                        tuple_value.append(array_from_str(array_str))
                    elif type_str := value.get("type"):
                        tuple_value.append(VirtualType(type_str))
                    else:
                        raise DeserializationError(f"Invalid Operand type {value}")

                operands[name] = tuple(tuple_value)
            return CombineRegistersNode(
                VirtualType(data["output_type"]),
                data["output_register_name"],
                int(data["num_output_subsystems"]),
                operands,
            )


class ConversionNodeSerializer(TypeSerializer[ConversionNode]):
    """Serializer for :class:`~.ConversionNode`."""

    TYPE_ID = "4"

    class TSV1(DataSerializer[ConversionNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "existing_name": obj.existing_name,
                "existing_type": obj.existing_type.value,
                "new_name": obj.new_name,
                "new_type": obj.new_type.value,
                "num_subsystems": obj.num_subsystems,
                "remove_existing": str(obj.remove_existing),
            }

        @classmethod
        def deserialize(cls, data):
            return ConversionNode(
                data["existing_name"],
                VirtualType(data["existing_type"]),
                data["new_name"],
                VirtualType(data["new_type"]),
                int(data["num_subsystems"]),
                data["remove_existing"] == "True",
            )


class InjectNoiseNodeSerializer(TypeSerializer[InjectNoiseNode]):
    """Serializer for :class:`~.InjectNoiseNode`."""

    TYPE_ID = "5"

    class TSV1(DataSerializer[InjectNoiseNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "register_name": obj._register_name,  # noqa: SLF001
                "sign_register_name": obj._sign_register_name,  # noqa: SLF001
                "noise_ref": obj._noise_ref,  # noqa: SLF001
                "modifier_ref": obj._modifier_ref,  # noqa: SLF001
                "num_subsystems": str(obj._num_subsystems),  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            return InjectNoiseNode(
                data["register_name"],
                data["sign_register_name"],
                data["noise_ref"],
                int(data["num_subsystems"]),
                data["modifier_ref"],
            )


class LeftMultiplicationNodeSerializer(TypeSerializer[LeftMultiplicationNode]):
    """Serializer for :class:`~.LeftMultiplicationNode`."""

    TYPE_ID = "6"

    class TSV1(DataSerializer[LeftMultiplicationNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "operand": orjson.dumps(obj._operand.to_json_dict()).decode("utf-8"),  # noqa: SLF001
                "register_name": obj._register_name,  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            return LeftMultiplicationNode(
                virtual_register_from_json(orjson.loads(data["operand"])),
                data["register_name"],
            )


class RightMultiplicationNodeSerializer(TypeSerializer[RightMultiplicationNode]):
    """Serializer for :class:`~.RightMultiplicationNode`."""

    TYPE_ID = "7"

    class TSV1(DataSerializer[RightMultiplicationNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "operand": orjson.dumps(obj._operand.to_json_dict()).decode("utf-8"),  # noqa: SLF001
                "register_name": obj._register_name,  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            return RightMultiplicationNode(
                virtual_register_from_json(orjson.loads(data["operand"])),
                data["register_name"],
            )


class PauliPastCliffordNodeSerializer(TypeSerializer[PauliPastCliffordNode]):
    """Serializer for :class:`~.PauliPastCliffordNode`."""

    TYPE_ID = "8"

    class TSV1(DataSerializer[PauliPastCliffordNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "op_name": obj._op_name,  # noqa: SLF001
                "subsystem_idxs": array_to_str(obj._subsystem_idxs),  # noqa: SLF001
                "register_name": obj._register_name,  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            return PauliPastCliffordNode(
                data["op_name"],
                data["register_name"],
                array_from_str(data["subsystem_idxs"]),
            )


class SliceRegisterNodeSerializer(TypeSerializer[SliceRegisterNode]):
    """Serializer for :class:`~.SliceRegisterNode`."""

    TYPE_ID = "9"

    class TSV1(DataSerializer[SliceRegisterNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            if isinstance(obj._slice_idxs, slice):  # noqa: SLF001
                is_slice = "true"
                slice_idxs = slice_to_json(obj._slice_idxs)  # noqa: SLF001
            else:
                is_slice = "false"
                slice_idxs = array_to_str(obj._slice_idxs)  # noqa: SLF001
            return {
                "input_type": obj._input_type.value,  # noqa: SLF001
                "output_type": obj._output_type.value,  # noqa: SLF001
                "input_register_name": obj._input_register_name,  # noqa: SLF001
                "output_register_name": obj._output_register_name,  # noqa: SLF001
                "slice_idxs": slice_idxs,
                "is_slice": is_slice,
            }

        @classmethod
        def deserialize(cls, data):
            slice_idxs = (
                slice_from_json(data["slice_idxs"])
                if data["is_slice"] == "true"
                else array_from_str(data["slice_idxs"])
            )
            return SliceRegisterNode(
                VirtualType(data["input_type"]),
                VirtualType(data["output_type"]),
                data["input_register_name"],
                data["output_register_name"],
                slice_idxs,
            )


class TwirlSamplingNodeSerializer(TypeSerializer[TwirlSamplingNode]):
    """Serializer for :class:`~.TwirlSamplingNode`."""

    TYPE_ID = "10"

    class TSV1(DataSerializer[TwirlSamplingNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            if isinstance(obj._distribution, HaarU2):  # noqa: SLF001
                distribution_type = "haar_u2"
            else:
                distribution_type = "pauli_uniform"
            distribution = {
                "type": distribution_type,
                "num_subsystems": obj._distribution.num_subsystems,  # noqa: SLF001
            }
            return {
                "lhs_register_name": obj._lhs_register_name,  # noqa: SLF001
                "rhs_register_name": obj._rhs_register_name,  # noqa: SLF001
                "distribution": orjson.dumps(distribution).decode("utf-8"),
            }

        @classmethod
        def deserialize(cls, data):
            distribution_dict = orjson.loads(data["distribution"])
            if distribution_dict["type"] == "haar_u2":
                distribution = HaarU2(distribution_dict["num_subsystems"])
            else:
                distribution = UniformPauli(distribution_dict["num_subsystems"])
            return TwirlSamplingNode(
                data["lhs_register_name"], data["rhs_register_name"], distribution
            )


class LeftU2ParametricMultiplicationNodeSerializer(
    TypeSerializer[LeftU2ParametricMultiplicationNode]
):
    """Serializer for :class:`~.LeftU2ParametricMultiplicationNode`."""

    TYPE_ID = "11"

    class TSV1(DataSerializer[LeftU2ParametricMultiplicationNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "operand": obj._operand,  # noqa: SLF001
                "param_indices": orjson.dumps(obj._param_idxs).decode("utf-8"),  # noqa: SLF001
                "register_name": obj._register_name,  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            return LeftU2ParametricMultiplicationNode(
                data["operand"],
                data["register_name"],
                orjson.loads(data["param_indices"]),
            )


class RightU2ParametricMultiplicationNodeSerializer(
    TypeSerializer[RightU2ParametricMultiplicationNode]
):
    """Serializer for :class:`~.RightU2ParametricMultiplicationNode`."""

    TYPE_ID = "12"

    class TSV1(DataSerializer[RightU2ParametricMultiplicationNode]):
        TSV = 1

        @classmethod
        def serialize(cls, obj):
            return {
                "operand": obj._operand,  # noqa: SLF001
                "param_indices": orjson.dumps(obj._param_idxs).decode("utf-8"),  # noqa: SLF001
                "register_name": obj._register_name,  # noqa: SLF001
            }

        @classmethod
        def deserialize(cls, data):
            return RightU2ParametricMultiplicationNode(
                data["operand"],
                data["register_name"],
                orjson.loads(data["param_indices"]),
            )
