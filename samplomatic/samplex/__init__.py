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

r""":class:`~.Samplex` is the core type of the samplomatic library.

In abstract terms, a samplex represents a parametric probability distribution over the parameters of
some template circuit, as well as other array-valued fields to be used in post-processing data
collected from executing the bound circuit.
In practical terms, it implements a :meth:`~.Samplex.sample` method that draws from this
distribution to produce random angles valid for the template circuit, along with the other fields.
For example, a samplex instance might implement Pauli-twirling all the layers of a circuit.
However, its semantics are not limited to this, and its structure is highly extensible: new group
types, new distributions, etc. can be added to the library.

Internally, a samplex uses a directed acycle graph (DAG) representation that procedurally describes
the sampling process.
Each node of the graph interacts with a collection of :class:`~.VirtualRegister`\s, and connections
between nodes denote register dependency: if :math:`A \rightarrow B`, then :math:`B` requires
:math:`A` to have acted on the registers before it is allowed to act.
There are three types of nodes:

 * :class:`~.SamplingNode`\s are responsible for instantiating new registers from inputs.
 * :class:`~.EvaluationNode`\s are responsible for transforming, combining, and removing registers.
 * :class:`~.CollectionNode`\s are responsible reading registers and writing to output values
   of :meth:`~.Samplex.sample`.
"""

from .interfaces import SamplexOutput
from .parameter_expression_table import ParameterExpressionTable
from .samplex import Samplex
from .samplex_serialization import samplex_from_json, samplex_to_json
