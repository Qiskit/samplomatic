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

"""Test analyze if else"""

from qiskit.circuit import QuantumCircuit

from samplomatic.transpiler.passes.analyze_if_else import analyze_branch, make_twirlable

# TODO: Complete testing of the function analyze_if_else()
# TODO: Complete testing of the IfElseOp in the tests of make_twirlable()


class TestMakeTwirlable:
    """Test the helper function ``make_twirlable``"""

    def test_already_twirlable_left(self):
        """Test a conditional that is already twirlable with left dressing"""
        qc = QuantumCircuit(2, 2)
        with qc.if_test((qc.clbits[0], 1)) as _else:
            qc.x(1)
            qc.cx(0, 1)
        with _else:
            qc.sx(0)
            qc.cz(1, 0)
        instr = qc[0]
        if_spec = analyze_branch(instr.operation.params[0])
        else_spec = analyze_branch(instr.operation.params[1])
        result = make_twirlable(instr, if_spec, else_spec, "left")
        assert result.instr is None

    def test_already_twirlable_right(self):
        """Test a conditional that is already twirlable with right dressing"""
        qc = QuantumCircuit(2, 2)
        with qc.if_test((qc.clbits[0], 1)) as _else:
            qc.cx(0, 1)
            qc.x(1)
        with _else:
            qc.cz(1, 0)
            qc.sx(0)
        instr = qc[0]
        if_spec = analyze_branch(instr.operation.params[0])
        else_spec = analyze_branch(instr.operation.params[1])
        result = make_twirlable(instr, if_spec, else_spec, "right")
        assert result.instr is None

    def test_not_twirlable_right(self):
        """Test a conditional that is not twirlable with right dressing"""
        qc = QuantumCircuit(2, 2)
        with qc.if_test((qc.clbits[0], 1)) as _else:
            qc.x(1)
            qc.cx(0, 1)
        with _else:
            qc.sx(1)
            qc.cz(1, 0)
        instr = qc[0]
        if_spec = analyze_branch(instr.operation.params[0])
        else_spec = analyze_branch(instr.operation.params[1])
        result = make_twirlable(instr, if_spec, else_spec, "right")
        assert result is None

    def test_not_twirlable_left(self):
        """Test a conditional that is not twirlable with left dressing"""
        qc = QuantumCircuit(2, 2)
        with qc.if_test((qc.clbits[0], 1)) as _else:
            qc.cx(0, 1)
            qc.x(1)
        with _else:
            qc.cz(1, 0)
            qc.sx(1)
        instr = qc[0]
        if_spec = analyze_branch(instr.operation.params[0])
        else_spec = analyze_branch(instr.operation.params[1])
        result = make_twirlable(instr, if_spec, else_spec, "left")
        assert result is None

    def test_can_make_twirlable_left(self):
        """Test a conditional that can be made twirlable with left dressing"""
        qc = QuantumCircuit(2, 2)
        with qc.if_test((qc.clbits[0], 1)) as _else:
            qc.sx(1)
            qc.cx(0, 1)
            qc.h(0)
        with _else:
            qc.sx(0)
            qc.x(1)
        instr = qc[0]
        if_spec = analyze_branch(instr.operation.params[0])
        else_spec = analyze_branch(instr.operation.params[1])
        result = make_twirlable(instr, if_spec, else_spec, "left")
        assert len(result.additional_1q_ops) == 1
        assert result.additional_1q_ops[0].qubits == (qc.qubits[0],)
        assert result.additional_1q_ops[0].operation.name == "h"

    def test_can_make_twirlable_right(self):
        """Test a conditional that can be made twirlable with right dressing"""
        qc = QuantumCircuit(2, 2)
        with qc.if_test((qc.clbits[0], 1)) as _else:
            qc.x(1)
            qc.cx(0, 1)
            qc.h(0)
        with _else:
            qc.sx(0)
            qc.sx(1)
        instr = qc[0]
        if_spec = analyze_branch(instr.operation.params[0])
        else_spec = analyze_branch(instr.operation.params[1])
        result = make_twirlable(instr, if_spec, else_spec, "right")
        assert len(result.additional_1q_ops) == 1
        assert result.additional_1q_ops[0].qubits == (qc.qubits[1],)
        assert result.additional_1q_ops[0].operation.name == "x"


class TestAnalyzeBranch:
    """Test the helper function ``analyze_branch``"""

    def test_1q_2q_1q(self):
        """Test 1q-2q-1q pattern"""
        circ = QuantumCircuit(2)
        circ.x(0)
        circ.sx(0)
        circ.sx(1)
        circ.h(1)
        circ.cx(0, 1)
        circ.cz(1, 0)
        circ.h(0)
        circ.rz(1.2, 0)
        circ.x(1)
        circ.rx(1.2, 1)

        expected_leading = {circ.qubits[0]: [0, 1], circ.qubits[1]: [2, 3]}
        expected_trailing = {circ.qubits[0]: [6, 7], circ.qubits[1]: [8, 9]}
        expected_is_2q = {circ.qubits[0]: True, circ.qubits[1]: True}
        res = analyze_branch(circ)
        assert res.leading_1q == expected_leading
        assert res.trailing_1q == expected_trailing
        assert res.is_2q == expected_is_2q

    def test_1q_2q(self):
        """Test 1q-2q pattern"""
        circ = QuantumCircuit(2)
        circ.x(0)
        circ.sx(0)
        circ.sx(1)
        circ.h(1)
        circ.cx(0, 1)
        circ.cz(1, 0)

        expected_leading = {circ.qubits[0]: [0, 1], circ.qubits[1]: [2, 3]}
        expected_trailing = {}
        expected_is_2q = {circ.qubits[0]: True, circ.qubits[1]: True}
        res = analyze_branch(circ)
        assert res.leading_1q == expected_leading
        assert res.trailing_1q == expected_trailing
        assert res.is_2q == expected_is_2q

    def test_2q_1q(self):
        """Test 2q-1q pattern"""
        circ = QuantumCircuit(2)
        circ.cx(0, 1)
        circ.cz(1, 0)
        circ.h(0)
        circ.rz(1.2, 0)
        circ.x(1)
        circ.rx(1.2, 1)

        expected_leading = {}
        expected_trailing = {circ.qubits[0]: [2, 3], circ.qubits[1]: [4, 5]}
        expected_is_2q = {circ.qubits[0]: True, circ.qubits[1]: True}
        res = analyze_branch(circ)
        assert res.leading_1q == expected_leading
        assert res.trailing_1q == expected_trailing
        assert res.is_2q == expected_is_2q

    def test_1q(self):
        """Test 1q pattern"""
        circ = QuantumCircuit(2)
        circ.h(0)
        circ.rz(1.2, 0)
        circ.x(1)
        circ.rx(1.2, 1)

        expected_leading = {circ.qubits[0]: [0, 1], circ.qubits[1]: [2, 3]}
        expected_trailing = {}
        expected_is_2q = {}
        res = analyze_branch(circ)
        assert res.leading_1q == expected_leading
        assert res.trailing_1q == expected_trailing
        assert res.is_2q == expected_is_2q

    def test_barriers_are_ignored(self):
        """Test that barriers (and alike) are ignored"""
        circ = QuantumCircuit(2)
        circ.barrier(0)
        circ.id(0)
        circ.delay(1, 0)

        expected_leading = {}
        expected_trailing = {}
        expected_is_2q = {}
        res = analyze_branch(circ)
        assert res.leading_1q == expected_leading
        assert res.trailing_1q == expected_trailing
        assert res.is_2q == expected_is_2q

    def test_1q_2q_1q_2q(self):
        """Test 1q-2q-1q-2q pattern"""
        circ = QuantumCircuit(2)
        circ.x(0)
        circ.cx(0, 1)
        circ.h(0)
        circ.cx(0, 1)

        assert analyze_branch(circ) is None
