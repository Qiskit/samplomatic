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

"""Samplex serialization.

:class:`~.Samplex` objects can be serialized to and from JSON via :func:`~.samplex_to_json` and
:func:`~.samplex_from_json`. The underlying format is a JSON node-link representation of the
samplex graph, produced by :func:`rustworkx.node_link_json`. Graph attributes encode data model
elements that live outside the graph itself (e.g. parameter tables and I/O specifications), and
node attributes encode the :class:`~.Node` type and its data. Samplexes have no edge attributes.

.. code-block:: python

    from samplomatic.serialization import samplex_to_json, samplex_from_json

    # save to a file
    samplex_to_json(samplex, filename="my_samplex.json")

    # or get a string
    json_str = samplex_to_json(samplex)

    # load from a string
    samplex = samplex_from_json(json_str)

Versioning
----------

Every serialized samplex encodes a Samplex Serialization Version (SSV), a single integer that
tracks changes to the serialization format independently of the package version. The constant
:const:`~.SSV` is the latest version known to the current package.

The SSV history is summarized in the following table:

.. list-table::
   :header-rows: 1

   * - SSV
     - Package version
     - Changes
   * - 1
     - 0.12.0
     - Initial SSV system; baseline serialization of all node and register types.
   * - 2
     - 0.14.0
     - Added :class:`~.C1Register` serialization; updated :class:`~.BasisChange` format.
   * - 3
     - 0.16.0
     - Added :class:`~.BalancedUniformPauli` distribution support in twirl nodes.

Backwards compatibility
^^^^^^^^^^^^^^^^^^^^^^^

A samplex written at a given SSV can be loaded by any package version whose :const:`~.SSV` is
greater than or equal to the one encoded in the file. In general, upgrading samplomatic should
preserve your ability to load previously saved samplexes, though support for very old SSVs may
eventually be dropped.

Loading a samplex written with a *future* SSV (i.e. by a newer version of samplomatic than you
have installed) will raise :class:`~.SerializationError`.

Writing at an older SSV
^^^^^^^^^^^^^^^^^^^^^^^

By default, :func:`~.samplex_to_json` writes at the latest :const:`~.SSV`. You can pass an earlier
``ssv`` to produce output that is loadable by older versions of samplomatic:

.. code-block:: python

    # write in a format compatible with samplomatic 0.12.0+
    samplex_to_json(samplex, filename="old_format.json", ssv=1)

This will raise :class:`~.SerializationError` if the samplex contains types that were introduced
after the requested SSV (e.g. a :class:`~.C1Register` cannot be written at SSV 1).
"""

from .samplex_serializer import samplex_from_json, samplex_to_json
