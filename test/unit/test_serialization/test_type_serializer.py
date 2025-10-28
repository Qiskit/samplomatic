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

import pytest

from samplomatic.exceptions import SerializationError
from samplomatic.serialization.type_serializer import DataSerializer, TypeSerializer


class TestTypeSerializerMeta:
    """Test the errors in new for the TypeSerializerMeta class."""

    def test_no_type_id_error(self):
        """Test that having no type id errors."""
        with pytest.raises(TypeError, match="without a type id."):

            class _(TypeSerializer):
                pass

    def test_duplicate_type_id_error(self):
        """Test that having duplicate type ids errors."""

        class _(TypeSerializer):
            TYPE_ID = "t0"

        with pytest.raises(TypeError, match="with the existing type id t0"):

            class _(TypeSerializer):
                TYPE_ID = "t0"

    def test_no_min_ssv_error(self):
        """Test that having no SSV errors."""
        with pytest.raises(TypeError, match="must specify a MIN_SSV"):

            class _(TypeSerializer):
                TYPE_ID = "t1"

                class MyDataSerializer(DataSerializer):
                    pass

    def test_overlapping_ssvs_error(self):
        """Test that having overlapping SSVs errors."""
        with pytest.raises(TypeError, match="multiple serializers for SSVs"):

            class _(TypeSerializer):
                TYPE_ID = "t2"

                class MyDataSerializer(DataSerializer):
                    MIN_SSV = 1
                    MAX_SSV = 2

                class MyOtherDataSerializer(DataSerializer):
                    MIN_SSV = 2
                    MAX_SSV = 2

    def test_missing_ssvs_error(self):
        """Test that having a gap in SSVs errors."""
        with pytest.raises(TypeError, match="missing a data serializer"):

            class _(TypeSerializer):
                TYPE_ID = "t3"

                class MyDataSerializer(DataSerializer):
                    MIN_SSV = 1
                    MAX_SSV = 1

                class MyOtherDataSerializer(DataSerializer):
                    MIN_SSV = 99
                    MAX_SSV = 100


class DummyTypeSerializer(TypeSerializer):
    """A dummy type serializer for tests."""

    TYPE_ID = "MY_TYPE"

    class OldSerializer(DataSerializer):
        MIN_SSV = 2
        MAX_SSV = 3

        @classmethod
        def serialize(cls, obj):
            return {"old": "old"}

        @classmethod
        def deserialize(cls, data):
            return "old"

    class NewSerializer(DataSerializer):
        MIN_SSV = 4
        MAX_SSV = 4

        @classmethod
        def serialize(cls, obj):
            return {"new": "new"}

        @classmethod
        def deserialize(cls, data):
            return "new"


class TestTypeSerializer:
    """Tests for the TypeSerializer class."""

    def test_serialize(self):
        """Test the serialize method."""
        assert DummyTypeSerializer.serialize("old", 2) == {
            "id": "MY_TYPE",
            "ssv": "2",
            "old": "old",
        }
        assert DummyTypeSerializer.serialize("old", 3) == {
            "id": "MY_TYPE",
            "ssv": "3",
            "old": "old",
        }
        assert DummyTypeSerializer.serialize("new", 4) == {
            "id": "MY_TYPE",
            "ssv": "4",
            "new": "new",
        }

    def test_serialize_errors(self):
        """Test the errors raised by the serialize method."""
        with pytest.raises(SerializationError, match="SSV greater than or equal to 2"):
            DummyTypeSerializer.serialize("old", 1)

        with pytest.raises(SerializationError, match="SSV less than or equal to 4"):
            DummyTypeSerializer.serialize("old", 5)

    def test_deserialize(self):
        """Test the deserialize method."""
        assert DummyTypeSerializer.deserialize({"id": "MY_TYPE", "ssv": "2", "old": "old"}) == "old"
        assert DummyTypeSerializer.deserialize({"id": "MY_TYPE", "ssv": "3", "old": "old"}) == "old"
        assert DummyTypeSerializer.deserialize({"id": "MY_TYPE", "ssv": "4", "new": "new"}) == "new"

    def test_deserialize_errors(self):
        """Test the errors raised by the deserialize method."""
        with pytest.raises(SerializationError, match="minimum supported by this serializer is 2"):
            DummyTypeSerializer.deserialize({"id": "MY_TYPE", "ssv": "1", "old": "old"})

        with pytest.raises(SerializationError, match="maximum supported by this serializer is 4"):
            DummyTypeSerializer.deserialize({"id": "MY_TYPE", "ssv": "5", "old": "old"})
