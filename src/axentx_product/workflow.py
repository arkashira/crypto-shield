"""
Crypto Shield Workflow Engine.

Handles transaction submission, approval logic, and audit logging.
"""
from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class Transaction:
    """Represents a crypto transaction."""
    id: str
    amount: float
    status: str = "pending"  # pending, approved, rejected
    approvers: Set[str] = field(default_factory=set)

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")


class WorkflowEngine:
    """
    Manages the lifecycle of crypto transactions.
    
    Enforces a minimum approval threshold before transactions are marked as approved.
    """
    def __init__(self, threshold: float, approvers: List[str]):
        self.threshold = threshold
        self.approvers = set(approvers)
        self.queue: List[Transaction] = []
        self.audit_log: List[str] = []

    def submit(self, transaction: Transaction) -> None:
        """Submit a new transaction to the workflow."""
        self.queue.append(transaction)
        self._log(f"Transaction {transaction.id} submitted for {transaction.amount}")

    def approve(self, transaction_id: str, approver: str) -> bool:
        """
        Attempt to approve a transaction.
        
        Returns True if the transaction was approved, False otherwise.
        """
        if approver not in self.approvers:
            self._log(f"Approval denied: {approver} is not an authorized approver.")
            return False

        transaction = next((t for t in self.queue if t.id == transaction_id), None)
        if not transaction:
            self._log(f"Approval failed: Transaction {transaction_id} not found.")
            return False

        if transaction.status != "pending":
            self._log(f"Approval failed: Transaction {transaction_id} is already {transaction.status}.")
            return False

        transaction.approvers.add(approver)

        # Check threshold
        if len(transaction.approvers) >= self.threshold:
            transaction.status = "approved"
            self._log(f"Transaction {transaction_id} approved by {approver}.")
            return True
        else:
            self._log(f"Transaction {transaction_id} pending. Current approvers: {len(transaction.approvers)}/{self.threshold}")
            return False

    def _log(self, message: str) -> None:
        """Record an event to the immutable audit log."""
        self.audit_log.append(message)

    def get_transaction(self, transaction_id: str) -> Transaction | None:
        """Retrieve a transaction by ID."""
        return next((t for t in self.queue if t.id == transaction_id), None)

    def get_audit_log(self) -> List[str]:
        """Return the immutable audit log."""
        return list(self.audit_log)
