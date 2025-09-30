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
from qiskit.transpiler.exceptions import TranspilerError
from qiskit.transpiler.passes import RemoveBarriers

from .noise_injection_strategies import NoiseInjectionStrategyLiteral
from .passes import (
    AddInjectNoise,
    AddTerminalRightDressedBoxes,
    GroupGatesIntoBoxes,
    GroupMeasIntoBoxes,
)
from .passes.insert_noops import AddNoopsActiveAccum, AddNoopsActiveCircuit, AddNoopsAll
from .twirling_strategies import TwirlingStrategyLiteral


def generate_boxing_pass_manager(
    enable_gates: bool = True,
    enable_measure: bool = True,
    measure_annotations: str = "twirl",
    twirling_strategy: TwirlingStrategyLiteral = "active",
    inject_noise_targets: Literal["none", "gates", "measures", "all"] = "none",
    inject_noise_strategy: NoiseInjectionStrategyLiteral = "no_modification",
    remove_barriers: bool = True,
) -> PassManager:
    """Generate a pass manager to group the operations in a circuit into boxes.

    Args:
        enable_gates: Whether to collect single- and multi-qubit gates into boxes using the
            :class:`~.GroupGatesIntoBoxes` pass.
        enable_measure: Whether to collect measurements into boxes using the
            :class:`~.GroupMeasIntoBoxes` pass.
        measure_annotations: The annotations placed on the measurement boxes by
            :class:`~.GroupMeasIntoBoxes` when ``enable_measure`` is ``True``. The supported values
            are:

                * ``'twirl'`` for a :class:`~.Twirl` annotation.
                * ``'basis_transform'`` for a :class:`~.BasisTransform` annotation with mode
                  ``measure``.
                * ``'all'`` for both :class:`~.Twirl` and :class:`~.BasisTransform` annotations.

        twirling_strategy: The twirling strategy.
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

        inject_noise_strategy: The noise injection strategy for the :class:`~.AddInjectNoise` pass.
        remove_barriers: Whether to apply the :class:`~.RemoveBarriers` pass to the input circuit
            before beginning to group gates and measurements into boxes. Setting this to ``True``
            generally leads to a smaller number of boxes in the output circuits.

    Returns:
        A pass manager that groups operations into boxes.

    Raises:
        TranspilerError: If the user selects a combination of inputs that is not supported.
    """
    passes = [RemoveBarriers()] if remove_barriers else []

    if enable_gates:
        passes.append(GroupGatesIntoBoxes())

    if enable_measure:
        passes.append(GroupMeasIntoBoxes(measure_annotations))

    if twirling_strategy == "active":
        pass
    elif twirling_strategy == "active-accum":
        passes.append(AddNoopsActiveAccum())
    elif twirling_strategy == "active-circuit":
        passes.append(AddNoopsActiveCircuit())
    elif twirling_strategy == "all":
        passes.append(AddNoopsAll())
    else:
        raise TranspilerError(
            f"``twirling_strategy = '{twirling_strategy}'`` is not supported."
            "The supported values are "
            f"{[strategy.name.lower() for strategy in TwirlingStrategyLiteral]}."
        )

    passes.append(AddTerminalRightDressedBoxes())
    passes.append(AddInjectNoise(strategy=inject_noise_strategy, targets=inject_noise_targets))

    return PassManager(passes)
