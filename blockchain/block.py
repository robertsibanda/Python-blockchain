import hashlib
from dataclasses import dataclass
from typing import List, Optional


class Block:
    """A block in the blockchain containing transactions and a header."""

    def __init__(self, _hash: str = '', prev_hash: str = '', transactions: Optional[List] = None):
        if transactions is None:
            transactions = []
        self.transactions = transactions
        self.header = {'hash': _hash, 'prev_hash': prev_hash, 'data_hash': ''}

    def add_new_transaction(self, transaction) -> None:
        """Append a transaction to the block's transaction list."""
        self.transactions.append(transaction)

    def create_block_data_hash(self, data: List[str]) -> None:
        """Compute SHA-256 hash over the provided data items and store as data_hash."""
        hasher = hashlib.sha256()
        [hasher.update(item.encode('utf-8')) for item in data]
        self.header['data_hash'] = hasher.hexdigest()

    def close_block(self) -> None:
        """Finalize the block by computing the data hash from all transaction hashes."""
        transaction_hashes = [tx.hash for tx in self.transactions]
        self.create_block_data_hash(transaction_hashes)


@dataclass(kw_only=True)
class HashBlock:
    """A lightweight hash-only representation of a block for chain comparison."""

    hash: str
    prev_hash: str
    data_hash: str

    def __hash__(self):
        return hash(f"{self.hash},{self.prev_hash},{self.data_hash}")
