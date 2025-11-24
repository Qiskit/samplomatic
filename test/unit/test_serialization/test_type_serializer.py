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
from samplomatic.serializable import TYPE_REGISTRY
from samplomatic.serialization.type_serializer import DataSerializer, TypeSerializer


@pytest.fixture
def restore_registry():
    """Ensure that a test doesn't mutate the registry."""
    original_id_registry = TypeSerializer.TYPE_ID_REGISTRY.copy()
    original_type_registry = TypeSerializer.TYPE_REGISTRY.copy()
    yield
    # for extra safety, don't even change the dictionary instance
    TypeSerializer.TYPE_ID_REGISTRY.clear()
    TypeSerializer.TYPE_ID_REGISTRY.update(original_id_registry)
    TypeSerializer.TYPE_REGISTRY.clear()
    TypeSerializer.TYPE_REGISTRY.update(original_type_registry)


class TestTypeSerializerMeta:
    """Test the errors in new for the TypeSerializerMeta class."""

    def test_no_type_id_error(self, restore_registry):
        """Test that having no type id errors."""
        with pytest.raises(TypeError, match="without a type id."):

            class _(TypeSerializer):
                pass

    def test_no_type_error(self, restore_registry):
        """Test that having no type errors."""
        with pytest.raises(TypeError, match="without a type."):

            class _(TypeSerializer):
                TYPE_ID = str
                pass

    def test_duplicate_type_id_error(self, restore_registry):
        """Test that having duplicate type ids errors."""

        class _(TypeSerializer):
            TYPE_ID = "MY_ID"
            TYPE = str

        with pytest.raises(TypeError, match="with the existing type id MY_ID"):

            class _(TypeSerializer):
                TYPE_ID = "MY_ID"
                TYPE = str

    def test_no_min_ssv_error(self, restore_registry):
        """Test that having no SSV errors."""
        with pytest.raises(TypeError, match="must specify a MIN_SSV"):

            class _(TypeSerializer):
                TYPE_ID = "MY_ID"
                TYPE = str

                class MyDataSerializer(DataSerializer):
                    pass

    def test_overlapping_ssvs_error(self, restore_registry):
        """Test that having overlapping SSVs errors."""
        with pytest.raises(TypeError, match="multiple serializers for SSVs"):

            class _(TypeSerializer):
                TYPE_ID = "MY_ID"
                TYPE = str

                class MyDataSerializer(DataSerializer):
                    MIN_SSV = 1
                    MAX_SSV = 2

                class MyOtherDataSerializer(DataSerializer):
                    MIN_SSV = 2
                    MAX_SSV = 2

    def test_missing_ssvs_error(self, restore_registry):
        """Test that having a gap in SSVs errors."""
        with pytest.raises(TypeError, match="missing a data serializer"):

            class _(TypeSerializer):
                TYPE_ID = "MY_ID"
                TYPE = str

                class MyDataSerializer(DataSerializer):
                    MIN_SSV = 1
                    MAX_SSV = 1

                class MyOtherDataSerializer(DataSerializer):
                    MIN_SSV = 99
                    MAX_SSV = 100


@pytest.fixture
def dummy_serializer():
    """Yield a dummy serializer then clear it from the type registry."""
    original_id_registry = TypeSerializer.TYPE_ID_REGISTRY.copy()
    original_type_registry = TypeSerializer.TYPE_REGISTRY.copy()

    class DummyTypeSerializer(TypeSerializer):
        """A dummy type serializer for tests."""

        TYPE_ID = "MY_TYPE"
        TYPE = str

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

    yield DummyTypeSerializer
    # for extra safety, don't even change the dictionary instance
    TypeSerializer.TYPE_ID_REGISTRY.clear()
    TypeSerializer.TYPE_ID_REGISTRY.update(original_id_registry)
    TypeSerializer.TYPE_REGISTRY.clear()
    TypeSerializer.TYPE_REGISTRY.update(original_type_registry)


class TestTypeSerializer:
    """Tests for the TypeSerializer class."""

    def test_registries(self):
        """Test that the TYPE_ID_REGISTRY has all elements of TYPE_REGISTRY."""
        assert TYPE_REGISTRY == set(TypeSerializer.TYPE_REGISTRY.keys())

    def test_serialize(self, dummy_serializer):
        """Test the serialize method."""
        assert dummy_serializer.serialize("old", 2) == {
            "id": "MY_TYPE",
            "ssv": "2",
            "old": "old",
        }
        assert dummy_serializer.serialize("old", 3) == {
            "id": "MY_TYPE",
            "ssv": "3",
            "old": "old",
        }
        assert dummy_serializer.serialize("new", 4) == {
            "id": "MY_TYPE",
            "ssv": "4",
            "new": "new",
        }

    def test_serialize_errors(self, dummy_serializer):
        """Test the errors raised by the serialize method."""
        with pytest.raises(SerializationError, match="SSV greater than or equal to 2"):
            dummy_serializer.serialize("old", 1)

        with pytest.raises(SerializationError, match="SSV less than or equal to 4"):
            dummy_serializer.serialize("old", 5)

    def test_deserialize(self, dummy_serializer):
        """Test the deserialize method."""
        assert dummy_serializer.deserialize({"id": "MY_TYPE", "ssv": "2", "old": "old"}) == "old"
        assert dummy_serializer.deserialize({"id": "MY_TYPE", "ssv": "3", "old": "old"}) == "old"
        assert dummy_serializer.deserialize({"id": "MY_TYPE", "ssv": "4", "new": "new"}) == "new"

    def test_deserialize_errors(self, dummy_serializer):
        """Test the errors raised by the deserialize method."""
        with pytest.raises(SerializationError, match="minimum supported by this serializer is 2"):
            dummy_serializer.deserialize({"id": "MY_TYPE", "ssv": "1", "old": "old"})

        with pytest.raises(SerializationError, match="maximum supported by this serializer is 4"):
            dummy_serializer.deserialize({"id": "MY_TYPE", "ssv": "5", "old": "old"})
