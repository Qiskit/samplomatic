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

"""Pytest fixtures for serialization tests"""

import pytest

from samplomatic.serialization.lookup_table_store import LookupTableStore, active_lookup_table_store


@pytest.fixture
def lookup_table_store():
    """Activate and yield an empty LookupTableStore for the duration of a test."""
    with active_lookup_table_store(store := LookupTableStore()):
        yield store
