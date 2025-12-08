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

"""generate_boxing_pass_manager"""

from typing import Literal

from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import RemoveBarriers

from ..utils import deprecate_arg, validate_literals
from .passes import (
    AbsorbSingleQubitGates,
    AddInjectNoise,
    AddTerminalRightDressedBoxes,
    GroupGatesIntoBoxes,
    GroupMeasIntoBoxes,
)
from .passes.insert_noops import AddNoopsActiveAccum, AddNoopsActiveCircuit, AddNoopsAll


@deprecate_arg(
    "remove_barriers",
    since="0.14.0",
    predicate=lambda remove_barriers: remove_barriers in {True, False},
    deprecation_description="Providing boolean values to the ``remove_barriers`` argument "
    "of ``generate_boxing_pass_manager()``",
    additional_msg="Instead, choose one of the string values.",
)
@validate_literals(
    "measure_annotations",
    "twirling_strategy",
    "inject_noise_targets",
    "inject_noise_strategy",
    "remove_barriers",
)
def generate_boxing_pass_manager(
    *,
    enable_gates: bool = True,
    enable_measures: bool = True,
    measure_annotations: Literal["twirl", "change_basis", "all"] = "twirl",
    twirling_strategy: Literal[
        "active", "active_accum", "active_circuit", "all"
    ] = "active_circuit",
    inject_noise_targets: Literal["none", "gates", "measures", "all"] = "none",
    inject_noise_strategy: Literal[
        "no_modification", "uniform_modification", "individual_modification"
    ] = "no_modification",
    remove_barriers: Literal[
        "immediately", "finally", "after_stratification", "never", True, False
    ] = "after_stratification",
) -> PassManager:
    """Construct a pass manager to group the operations in a circuit into boxes.

    This function can be used to construct a new :class:`qiskit.transpiler.PassManager` that
    puts the instructions of the circuit into annotated boxes.

    .. plot::
        :include-source:
        :context:

        >>> from qiskit.circuit import QuantumCircuit
        >>> from samplomatic.transpiler import generate_boxing_pass_manager
        >>>
        >>> # Create a simple circuit to test with
        >>> circuit = QuantumCircuit(3)
        >>> circuit.cz(0, 1)
        >>> circuit.cz(1, 2)
        >>> circuit.measure_all()
        >>>
        >>> pm = generate_boxing_pass_manager()
        >>>
        >>> boxed_circuit = pm.run(circuit)
        >>> boxed_circuit.draw("mpl") # doctest: +SKIP

    To group instructions into boxes, a pass manager returned by this function takes the following
    steps in order:

    * If ``remove_barriers`` is ``True``, it removes all the barriers in the input circuit
      using the :class:`qiskit.transpiler.passes.RemoveBarriers` pass.
    * If ``enable_gates`` is ``True``, using the :class:`~.GroupGatesIntoBoxes` pass,
      it creates boxes containing two-qubit gates. The resulting boxes are twirl-annotated and
      left-dressed, and contain a single layer of two-qubit gates.
    * If ``enable_measures`` is ``True``, it uses the :class:`~.GroupMeasIntoBoxes`
      pass to group the measurements. All the resulting boxes are left dressed. Depending
      on the value of ``measure_annotations``, they own a :class:`~.Twirl` annotation, a
      :class:`~.ChangeBasis` annotation, or both.
    * It adds idling qubits to the boxes following the given ``twirling_strategy``.
    * Using the :class:`~.AddTerminalRightDressedBoxes` pass, it adds empty right-dressed boxes
      to ensure that the resulting pass manager can produce circuits that can be successfully
      turned into a template/samplex pair by the :meth:`samplomatic.build` function.
    * It uses the :class:`~.AbsorbSingleQubitGates` pass to absorb any chains of single-qubit gates
      in the circuit into a box, left- or right-dressed, that immediately succeeds the chain. This
      will cause the gates to be folded into the dressing once the circuit is built.
    * If ``inject_noise_targets`` is not ``'none'``, it uses the
      :class:`~.AddInjectNoise` pass to replace boxes with new boxes that additionally have
      inject noise :class:`~.InjectNoise` annotations.

    Args:
        enable_gates: Whether to collect single- and multi-qubit gates into boxes using the
            :class:`~.GroupGatesIntoBoxes` pass.
        enable_measures: Whether to collect measurements into boxes using the
            :class:`~.GroupMeasIntoBoxes` pass.
        measure_annotations: The annotations placed on the measurement boxes by
            :class:`~.GroupMeasIntoBoxes` when ``enable_measures`` is ``True``. The supported values
            are:

            * ``'twirl'`` for a :class:`~.Twirl` annotation.
            * ``'change_basis'`` for a :class:`~.ChangeBasis` annotation with mode
              ``measure``.
            * ``'all'`` for both :class:`~.Twirl` and :class:`~.ChangeBasis` annotations.

        twirling_strategy: The strategy for whether and how twirling boxes are extended to
            include elligible idle qubits; the boxing pass manager begins by constructing twirling
            boxes that contain one layer of multi-qubit gates or measurements, preceded by all of
            the adjacent single-qubit gates, then, according to the value of this option, these
            boxes are extended idling qubits. The allowed values are:

            * ``'active'``: No idling qubits are added to the boxes, meaning that every box only
              twirls the qubits that are active within the box.
            * ``'active_accum'``: Idling qubits are added so that each individual box twirls all
              qubits that have been acted on by some instruction in the circuit up to and including
              the box.
            * ``'active_circuit'``: Idling qubits are added so that each individual box twirls all
              qubits acted on by any instruction in the circuit.
            * ``'all'``: Idling qubits are added so that each individual box twirls all of the
              qubits in the circuit.

        inject_noise_targets: The boxes to annotate with an :class:`~.InjectNoise` annotation
            using the :class:`~.AddInjectNoise` pass. The supported values are:

            * ``'none'`` to avoid annotating boxes of any kind.
            * ``'gates'`` to annotate all the twirled boxes that contain entanglers, such as
              those created by the :class:`~.GroupGatesIntoBoxes` pass, and avoid annotating
              all the other boxes.
            * ``'measures'`` to annotate all the twirled boxes that own a classical register,
              such as those created by the :class:`~.GroupMeasIntoBoxes` pass, and avoid
              annotating all the other boxes.
            * ``'all'`` to target all the twirl-annotated boxes that contain entanglers
              and/or own classical registers.

        inject_noise_strategy: The noise injection strategies supported by the
            :class:`~AddInjectNoise` pass. The following options are supported. In all these
            options, by "equivalent boxes" we mean boxes that are equal up to single-qubit qubit
            gates on the dressing side.

            * ``'no_modification'``: All the equivalent boxes are assigned an inject noise
              annotation with the same ``ref`` and with ``modifier_ref=''``.
            * ``'uniform_modification'``: All the equivalent boxes are assigned an inject noise
              annotation with the same ``ref`` and with ``modifier_ref=ref``.
            * ``'individual_modification'``: All the equivalent boxes are assigned an inject noise
              annotation with the same ``ref``. Every box is assigned a unique ``modifier_ref``.

        remove_barriers: When to apply the :class:`qiskit.transpiler.passes.RemoveBarriers` pass.
            All possible string values are:

            * ``'after_stratification'`` removes barriers, but only after entangler and
              measurement instructions have been boxed and extended with ``twirling_strategy``, and
              before single-qubit gates are boxed. This effectively allows barriers to be used as
              hints to choose the entangler and measurement content of boxes, while also letting
              single-qubit gates move freely past where there had been a barrier, allowing them be
              absorbed into adjacent boxes.
            * ``'immediately'`` removes barriers before doing anything else, so that existing
              barriers effectively have no role in box grouping.
            * ``'finally'`` removes barriers, but only as the very last step. This causes, for
              example, single-qubit gates that are trapped between barriers to not be placed
              into boxes.
            * ``'never'`` causes barriers to never be removed.

            Boolean values are deprecated such that ``True`` corresponds to ``'immediately'`` and
            ``False`` corresponds to ``'never'``.

    Returns:
        A pass manager that groups operations into boxes.

    Raises:
        TranspilerError: If the user selects a combination of inputs that is not supported.
    """
    # coerce legacy values of remove_barriers into equivalent string literal values
    if remove_barriers is True:
        remove_barriers = "immediately"
    elif remove_barriers is False:
        remove_barriers = "never"

    passes = []
    if remove_barriers == "immediately":
        passes.append(RemoveBarriers())

    if enable_gates:
        passes.append(GroupGatesIntoBoxes())

    if enable_measures:
        passes.append(GroupMeasIntoBoxes(measure_annotations))

    if twirling_strategy == "active":
        pass
    elif twirling_strategy == "active_accum":
        passes.append(AddNoopsActiveAccum())
    elif twirling_strategy == "active_circuit":
        passes.append(AddNoopsActiveCircuit())
    elif twirling_strategy == "all":
        passes.append(AddNoopsAll())

    passes.append(AddTerminalRightDressedBoxes())

    if remove_barriers == "after_stratification":
        passes.append(RemoveBarriers())

    passes.append(AbsorbSingleQubitGates())
    passes.append(AddInjectNoise(strategy=inject_noise_strategy, targets=inject_noise_targets))

    if remove_barriers == "finally":
        passes.append(RemoveBarriers())

    return PassManager(passes)
