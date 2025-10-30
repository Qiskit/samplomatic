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

"""Test the Samplex class"""

import threading
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pytest
from qiskit.circuit import Parameter

from samplomatic.exceptions import SamplexConstructionError, SamplexRuntimeError
from samplomatic.optionals import HAS_PLOTLY
from samplomatic.samplex import Samplex
from samplomatic.samplex.samplex import wait_with_raise
from samplomatic.tensor_interface import PauliLindbladMapSpecification, TensorSpecification
from samplomatic.virtual_registers import PauliRegister, U2Register


class TestBasic:
    """Basic tests to do with construction and attributes."""

    def _build_samplex(self, n_nodes, node_type, param) -> Samplex:
        """Return a basic samplex"""
        samplex = Samplex()
        for _ in range(n_nodes):
            samplex.add_node(node_type())
        for idx in range(n_nodes - 1):
            samplex.add_edge(idx, idx + 1)
        samplex.append_parameter_expression(param)
        samplex.add_input(TensorSpecification("a", (1, 2, "x"), np.uint8))
        samplex.add_output(TensorSpecification("out", ("num_randomizations", 5, 6), float))
        samplex.set_passthrough_params([(0, param)])
        return samplex

    def test_empty(self):
        """Test that an empty samplex doesn't error when sampled."""
        samplex = Samplex()
        samplex.finalize()

        samplex.sample(samplex.inputs())
        samplex.sample({})
        samplex.sample(None)

    def test_str(self):
        """Test the string dunder is doing fancy stuff."""
        samplex = Samplex()
        samplex.add_input(TensorSpecification("a", (1, 2, "x"), np.uint8))
        assert "Samplex" in str(samplex)
        assert "Inputs:" in str(samplex)
        assert "Outputs:" in str(samplex)

    def test_requires_finalize(self):
        """Test that we get an error when we try and sample without finalizing first."""
        samplex = Samplex()
        with pytest.raises(SamplexRuntimeError, match="The samplex has not been finalized yet"):
            samplex.sample(samplex.inputs())

    def test_finalize_chain(self):
        """Test that we can chain the finalize method because it returns self."""
        samplex = Samplex()
        assert samplex.finalize() is samplex

    def test_append_parametric_expression(self):
        """Test the method that appends parametric expressions."""
        samplex = Samplex()
        assert samplex.num_parameters == 0

        assert samplex.append_parameter_expression(a := Parameter("a")) == 0
        assert samplex.append_parameter_expression(b := Parameter("b")) == 1
        assert samplex.append_parameter_expression(a) == 2
        assert samplex.append_parameter_expression(a + b + Parameter("c")) == 3

        assert samplex.num_parameters == 3

    def test_add_output(self):
        """Test that we can add an output."""
        samplex = Samplex()
        samplex.add_output(TensorSpecification("out", ("num_randomizations", 5, 6), float))
        samplex.finalize()
        output = samplex.sample(samplex.inputs(), num_randomizations=11)
        assert set(output) == {"out"}
        assert output["out"].shape == (11, 5, 6)

    def test_add_output_fails(self):
        """Test that adding an output fails when it should."""
        samplex = Samplex()
        samplex.add_output(PauliLindbladMapSpecification("out", 2, 3))
        with pytest.raises(SamplexConstructionError, match="'out' already exists"):
            samplex.add_output(PauliLindbladMapSpecification("out", 8, 9))

    def test_add_node_fails(self, dummy_sampling_node):
        """Test that adding a node fails when expected."""
        samplex = Samplex()
        samplex.add_node(dummy_sampling_node())
        samplex.append_parameter_expression(Parameter("a"))
        with pytest.raises(SamplexConstructionError, match="index 4 .* 1 .* expressions so far"):
            samplex.add_node(dummy_sampling_node(parameter_idxs=[1, 4]))

    def test_add_node_undoes_finalize(self, dummy_sampling_node):
        """Test that adding a node causes the samplex to not be finalized."""
        samplex = Samplex()
        samplex.finalize()
        samplex.sample(samplex.inputs())
        samplex.add_node(dummy_sampling_node())
        with pytest.raises(SamplexRuntimeError, match="The samplex has not been finalized yet"):
            samplex.sample(samplex.inputs())

    def test_add_edge_undoes_finalize(self, dummy_collection_node, dummy_sampling_node):
        """Test that adding an edge causes the samplex to not be finalized."""
        samplex = Samplex()
        a = samplex.add_node(dummy_sampling_node())
        b = samplex.add_node(dummy_collection_node())
        samplex.finalize()
        samplex.sample(samplex.inputs())
        samplex.add_edge(a, b)
        with pytest.raises(SamplexRuntimeError, match="The samplex has not been finalized yet"):
            samplex.sample(samplex.inputs())

    @pytest.mark.skipif(not HAS_PLOTLY, reason="plotly is not installed")
    def test_draw(
        self, save_plot, dummy_collection_node, dummy_evaluation_node, dummy_sampling_node
    ):
        """Test the ``draw`` method."""
        samplex = Samplex()
        a = samplex.add_node(dummy_sampling_node(instantiates={"x": (10, PauliRegister)}))
        b = samplex.add_node(dummy_evaluation_node(reads_from={"y": ({6}, PauliRegister)}))
        c = samplex.add_node(dummy_collection_node(reads_from={"x": ({6}, PauliRegister)}))
        samplex.add_edge(a, b)
        samplex.add_edge(b, c)

        save_plot(samplex.draw())

    def test_equality(self, dummy_sampling_node, dummy_collection_node):
        """Test equality of Samplex objects"""
        param = Parameter("a")
        samplex = self._build_samplex(2, dummy_sampling_node, param)
        assert samplex == samplex
        assert samplex == self._build_samplex(2, dummy_sampling_node, param)
        assert samplex != self._build_samplex(2, dummy_sampling_node, Parameter("a"))

        new_samplex = self._build_samplex(3, dummy_sampling_node, param)
        assert samplex != new_samplex

        new_samplex = self._build_samplex(2, dummy_collection_node, param)
        assert samplex != new_samplex

        new_samplex = self._build_samplex(2, dummy_sampling_node, param)
        new_samplex.add_edge(1, 0)
        assert samplex != new_samplex

        new_samplex = self._build_samplex(2, dummy_sampling_node, param)
        new_samplex.add_input(TensorSpecification("b", (1, 2, "x"), np.uint8))
        assert samplex != new_samplex

        new_samplex = self._build_samplex(2, dummy_sampling_node, param)
        new_samplex.add_output(TensorSpecification("out2", (9,), float, "desc"))
        assert samplex != new_samplex

        new_samplex = self._build_samplex(2, dummy_sampling_node, param)
        new_samplex.append_parameter_expression(Parameter("x") + Parameter("d"))
        assert samplex != new_samplex

        new_samplex = self._build_samplex(2, dummy_sampling_node, param)
        new_samplex.set_passthrough_params([(1, Parameter("y"))])
        assert samplex != new_samplex

        new_samplex = self._build_samplex(2, dummy_sampling_node, param)
        new_samplex.finalize()
        assert samplex != new_samplex


class TestValidation:
    """Tests that check that validation failure mechanisms are working."""

    def test_use_of_uninitialized_in_evaluation(
        self, dummy_collection_node, dummy_evaluation_node, dummy_sampling_node
    ):
        """Test for failure when an evaluation node attempts to use an uninitialized register."""
        samplex = Samplex()
        a = samplex.add_node(dummy_sampling_node(instantiates={"x": (10, PauliRegister)}))
        b = samplex.add_node(dummy_evaluation_node(reads_from={"y": ({6}, PauliRegister)}))
        c = samplex.add_node(dummy_collection_node(reads_from={"x": ({6}, PauliRegister)}))
        samplex.add_edge(a, b)
        samplex.add_edge(b, c)
        with pytest.raises(
            SamplexConstructionError, match="read from register 'y'.* was not found."
        ):
            samplex.finalize()

    def test_use_of_uninitialized_in_collection(
        self, dummy_collection_node, dummy_evaluation_node, dummy_sampling_node
    ):
        """Test for failure when a collection node attempts to use an uninitialized register."""
        samplex = Samplex()
        a = samplex.add_node(dummy_sampling_node(instantiates={"x": (10, PauliRegister)}))
        b = samplex.add_node(dummy_evaluation_node(reads_from={"x": ({6}, PauliRegister)}))
        c = samplex.add_node(dummy_collection_node(reads_from={"y": ({6}, PauliRegister)}))
        samplex.add_edge(a, b)
        samplex.add_edge(b, c)
        with pytest.raises(
            SamplexConstructionError, match="read from register 'y'.* was not found."
        ):
            samplex.finalize()


class TestSample:
    """Tests for the sample method."""

    def test_keep_registers(self):
        """Test that the keep_registers sample argument works."""
        samplex = Samplex()
        samplex.finalize()
        output = samplex.sample(samplex.inputs())
        assert "registers" not in output

        samplex = Samplex()
        samplex.finalize()
        output = samplex.sample(samplex.inputs(), keep_registers=True)
        assert "registers" in output.metadata

    def test_single_component(
        self, dummy_collection_node, dummy_evaluation_node, dummy_sampling_node
    ):
        """Basic test with a simple linear graph and one component."""
        samplex = Samplex()

        samplex.add_output(TensorSpecification("out", (9,), float, "desc"))

        a = samplex.add_node(dummy_sampling_node(instantiates={"x": (10, PauliRegister)}))
        b = samplex.add_node(dummy_evaluation_node(reads_from={"x": ({6}, PauliRegister)}))
        c = samplex.add_node(dummy_evaluation_node(instantiates={"y": (15, PauliRegister)}))
        d = samplex.add_node(
            dummy_evaluation_node(
                instantiates={"z": (3, U2Register)}, reads_from={"y": ({8, 2}, PauliRegister)}
            )
        )
        e = samplex.add_node(
            dummy_collection_node(
                reads_from={"x": ({8}, PauliRegister)}, removes={"y"}, outputs_to={"out"}
            )
        )

        samplex.add_edge(a, b)
        samplex.add_edge(b, c)
        samplex.add_edge(c, d)
        samplex.add_edge(d, e)

        samplex.finalize()

        outputs = samplex.sample(samplex.inputs(), num_randomizations=13, keep_registers=True)
        assert set(outputs) == {"out"}
        assert set(outputs.metadata) == {"registers"}

        registers = outputs.metadata["registers"]
        assert set(registers) == {"x", "z"}

        assert isinstance(registers["x"], PauliRegister)
        assert registers["x"].shape == (10, 13)

        assert isinstance(registers["z"], U2Register)
        assert registers["z"].shape == (3, 1)

        assert np.allclose(outputs["out"], registers["x"].virtual_gates[8, 0])

    def test_two_components(
        self, dummy_collection_node, dummy_evaluation_node, dummy_sampling_node
    ):
        """Basic test with a simple linear graph and two components."""
        samplex = Samplex()

        a = samplex.add_node(dummy_collection_node(reads_from={"x": ({8}, PauliRegister)}))
        b = samplex.add_node(dummy_evaluation_node(writes_to={"x": ({8}, PauliRegister)}))
        c = samplex.add_node(
            dummy_sampling_node(instantiates={"x": (10, PauliRegister), "y": (15, U2Register)})
        )
        d = samplex.add_node(dummy_evaluation_node(writes_to={"y": ({6}, U2Register)}))
        e = samplex.add_node(dummy_collection_node(reads_from={"y": ({6}, U2Register)}))

        samplex.add_edge(a, b)
        samplex.add_edge(b, c)
        samplex.add_edge(c, d)
        samplex.add_edge(d, e)

        samplex.finalize()

        registers = samplex.sample(
            samplex.inputs(), num_randomizations=13, keep_registers=True
        ).metadata["registers"]
        assert set(registers) == {"x", "y"}

        assert isinstance(registers["x"], PauliRegister)
        assert registers["x"].shape == (10, 13)

        assert isinstance(registers["y"], U2Register)
        assert registers["y"].shape == (15, 13)

    @pytest.mark.parametrize("input_as_dict", [True, False])
    def test_parameter_evaluation(self, input_as_dict, dummy_evaluation_node, dummy_sampling_node):
        """Test the evaluation method when there are parameters."""
        samplex = Samplex()
        samplex.append_parameter_expression(a := Parameter("a"))
        samplex.append_parameter_expression(b := Parameter("b"))

        i = samplex.add_node(
            dummy_sampling_node(instantiates={"x": (15, PauliRegister), "y": (10, PauliRegister)})
        )
        j = samplex.add_node(
            dummy_evaluation_node(writes_to={"x": ({3, 6}, PauliRegister)}, parameter_idxs=[1, 0])
        )

        samplex.append_parameter_expression(a + b)
        samplex.append_parameter_expression(b + a + Parameter("c"))
        samplex.add_input(TensorSpecification("parameter_values", (3,), float))
        k = samplex.add_node(
            dummy_evaluation_node(
                writes_to={"y": ({2, 4, 6, 7}, PauliRegister)}, parameter_idxs=[3, 2, 0]
            )
        )

        samplex.add_edge(i, j)
        samplex.add_edge(j, k)

        samplex.finalize()

        if input_as_dict:
            samplex_input = {"parameter_values": np.array([1, 2, 4], float)}
        else:
            samplex_input = samplex.inputs().bind(parameter_values=np.array([1, 2, 4], float))

        registers = samplex.sample(
            samplex_input, num_randomizations=13, keep_registers=True
        ).metadata["registers"]
        assert set(registers) == {"x", "y"}

        assert isinstance(registers["x"], PauliRegister)
        assert registers["x"].shape == (15, 13)
        assert registers["x"].virtual_gates[3, 0] == 2  # pos 3 gets 1st param expr; b
        assert registers["x"].virtual_gates[6, 0] == 1  # pos 6 gets 0th param expr; a

        assert isinstance(registers["y"], PauliRegister)
        assert registers["y"].shape == (10, 13)
        assert registers["y"].virtual_gates[2, 0] == 7 % 4  # pos 2 gets 3rd param expr; a+b+c
        assert registers["y"].virtual_gates[4, 0] == 3  # pos 4 gets 2nd param expr; a+b
        assert registers["y"].virtual_gates[6, 0] == 1  # pos 6 gets 0th param expr; a

    def test_reraise_exceptions(self, dummy_sampling_error_node):
        """Test errors from nodes are properly raised."""
        samplex = Samplex()
        samplex.add_node(dummy_sampling_error_node())
        samplex.finalize()

        with pytest.raises(SamplexRuntimeError, match="This node cannot sample."):
            samplex.sample(samplex.inputs())

    def test_wait_with_raise_completes_all_tasks(self):
        """Test that wait_with_raise waits for all tasks to complete when no exception is raised."""
        results = []

        def task(x):
            results.append(x)
            return x

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(task, i) for i in range(3)]
            wait_with_raise(futures)
        assert sorted(results) == [0, 1, 2]
        assert all(f.done() for f in futures)

    def test_wait_with_raise_raises_on_exception(self):
        """Test that wait_with_raise raises the first exception from the futures."""

        def good_task():
            return 42

        def bad_task():
            raise ValueError("fail!")

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(good_task), executor.submit(bad_task)]
            with pytest.raises(ValueError, match="fail!"):
                wait_with_raise(futures)
            # All futures should be done or cancelled
            assert all(f.done() or f.cancelled() for f in futures)

    def test_wait_with_raise_cancels_remaining_on_exception(self):
        """Test that wait_with_raise cancels remaining tasks after an exception."""
        event = threading.Event()

        def slow_task():
            event.wait(timeout=1)
            return "slow"

        def fast_fail():
            raise RuntimeError("boom")

        with ThreadPoolExecutor(max_workers=2) as executor:
            f_fail = executor.submit(fast_fail)
            f_slow = executor.submit(slow_task)  # stays pending
            with pytest.raises(RuntimeError, match="boom"):
                wait_with_raise([f_fail, f_slow])
            # At least one future should be cancelled
            assert f_slow.cancelled()
