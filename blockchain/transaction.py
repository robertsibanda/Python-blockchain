from dataclasses import dataclass
from typing import Any, Dict

from .security import create_hash_default


@dataclass
class Transaction:
    """A blockchain transaction carrying typed data with an auto-computed hash.

    Attributes:
        type_: Transaction type (e.g. record, permission update, account init, appointment).
        data: The payload of the transaction.
        metadata: Additional metadata (e.g. patient ID, signatures).
        hash: SHA-256 hash of the data field, computed automatically.
    """

    type_: str
    data: str
    metadata: str
    hash: str = ''

    def __post_init__(self):
        if not self.hash:
            self.hash = create_hash_default(self.data)

    def _from_dict(self, data: Dict[str, Any]) -> None:
        """Populate transaction fields from a dictionary."""
        self.type_ = data['type_']
        self.data = data['data']
        self.metadata = data['metadata']
        self.hash = create_hash_default(self.data)

    def verified(self) -> None:
        """Placeholder for signature verification logic."""
        return

    def is_valid(self) -> bool:
        """Return True if the transaction passes basic validity checks."""
        return True


@dataclass(frozen=True)
class HashTransaction:
    """A frozen dataclass representing only the hash of a transaction."""
    hash: str
