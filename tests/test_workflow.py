"""
Tests for the Crypto Shield workflow engine.
"""
import pytest
from axentx_product.workflow import Transaction, WorkflowEngine


def test_submit_transaction():
    """Test that a transaction is added to the queue."""
    engine = WorkflowEngine(threshold=1, approvers=["Alice"])
    t = Transaction("tx1", 100.0)
    engine.submit(t)
    assert len(engine.queue) == 1
    assert engine.queue[0].id == "tx1"


def test_approval_threshold_met():
    """Test that a transaction is approved when the threshold is met."""
    engine = WorkflowEngine(threshold=2, approvers=["Alice", "Bob"])
    t = Transaction("tx2", 500.0)
    engine.submit(t)

    # Alice approves
    result = engine.approve("tx2", "Alice")
    assert result is False  # Not enough approvers yet
    assert t.status == "pending"

    # Bob approves
    result = engine.approve("tx2", "Bob")
    assert result is True
    assert t.status == "approved"


def test_approval_threshold_not_met():
    """Test that a transaction remains pending if threshold is not met."""
    engine = WorkflowEngine(threshold=2, approvers=["Alice"])
    t = Transaction("tx3", 50.0)
    engine.submit(t)

    result = engine.approve("tx3", "Alice")
    assert result is False
    assert t.status == "pending"


def test_unauthorized_approver():
    """Test that a non-approver cannot approve a transaction."""
    engine = WorkflowEngine(threshold=1, approvers=["Alice"])
    t = Transaction("tx4", 10.0)
    engine.submit(t)

    result = engine.approve("tx4", "Charlie")
    assert result is False
    assert t.status == "pending"


def test_duplicate_approval():
    """Test that the same approver cannot approve the same transaction twice."""
    engine = WorkflowEngine(threshold=1, approvers=["Alice"])
    t = Transaction("tx5", 20.0)
    engine.submit(t)

    engine.approve("tx5", "Alice")
    engine.approve("tx5", "Alice")  # Try again

    # Should still be pending because it was already approved once (or logic handles idempotency)
    # In this implementation, we check status before adding, so it should fail gracefully
    # or simply not change status. The logic in workflow.py checks status == "pending".
    assert t.status == "approved"  # It was approved once
    assert len(t.approvers) == 1


def test_audit_log():
    """Test that the audit log records events."""
    engine = WorkflowEngine(threshold=1, approvers=["Alice"])
    t = Transaction("tx6", 100.0)
    engine.submit(t)
    engine.approve("tx6", "Alice")

    logs = engine.get_audit_log()
    assert len(logs) == 2
    assert "submitted" in logs[0]
    assert "approved" in logs[1]


def test_negative_amount_raises_error():
    """Test that negative amounts are rejected."""
    with pytest.raises(ValueError):
        Transaction("tx7", -10.0)
