from dataclasses import dataclass, field
from typing import Optional
from .security import verify_data, create_hash_default


@dataclass
class Transaction:
    """
    transaction_type : represents the node-type 
    Not all transactions are stored on all nodes
    access logs - Node Type 1, access permissions - Node Type 2
    medical records - Node Type 3
    """
    type_: str
    data: str
    metadata: str
    hash: str

    def __post_init__(self):
        self.hash = create_hash_default(self.data)

    def _from_dict(self, data: dict):
        self.type_ = data['type_']
        self.data = data['data']
        self.metadata = data['metadata']
        self.hash = create_hash_default(self.data)

    def verified(self):
        # verify_data(self.data, self.metadata['signature'], self.metadata['pk'])
        return

    def is_valid(self) -> bool:
        # self.verified()
        return True


@dataclass(frozen=True)
class HashTransaction:
    hash: str
