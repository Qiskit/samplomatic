# This code is a Qiskit project.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Stratification problem representation.

This subpackage provides a self-contained intermediate representation for the
*hypergraph stratification* combinatorial problem: given a hypergraph ``H = (Q, E)``,
a partial order ``≺`` on ``E``, and a labelling ``σ : E → Σ``, find a minimum-depth
(or minimum unique-pattern-count) *stratification* — a sequence of *layers* that
partition ``E`` consistently with ``≺``.

The four public classes are:

- :class:`.Hypergraph` — the pair ``(Q, E)``.
- :class:`.StratificationInstance` — the full problem input ``(H, ≺, σ)``.
- :class:`.Layer` — a single valid layer (antichain + strong matching).
- :class:`.Stratification` — an ordered sequence of layers forming a complete stratification.

This module is algorithm-agnostic.  The solving algorithms are implemented separately and
may use their own internal representations, but should accept and return the classes defined
here at their boundaries.
"""

from .algorithms import (
    coffman_graham_stratify,
    grasp_stratify,
    greedy_stratify,
    ilp_stratify,
    pattern_batch_stratify,
    refine_stratification,
)
from .conversion import ConversionContext, EdgeKind, dag_to_instance, stratification_to_dag
from .hypergraph import Hypergraph
from .instance import StratificationInstance
from .orchestration import stratify_mixed, stratify_separate
from .stratification import Layer, Stratification

__all__ = [
    "ConversionContext",
    "EdgeKind",
    "Hypergraph",
    "Layer",
    "Stratification",
    "StratificationInstance",
    "coffman_graham_stratify",
    "dag_to_instance",
    "grasp_stratify",
    "greedy_stratify",
    "ilp_stratify",
    "pattern_batch_stratify",
    "refine_stratification",
    "stratification_to_dag",
    "stratify_mixed",
    "stratify_separate",
]
