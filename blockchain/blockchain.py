import hashlib
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from .block import Block, HashBlock


def create_hash(data: Any) -> str:
    """Compute a SHA-256 hex digest of the given data."""
    return hashlib.sha256(f'{data}'.encode('utf-8')).hexdigest()


class Chain:
    """A blockchain composed of linked blocks, starting with a genesis block."""

    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def refresh_block(self) -> bool:
        """Check the validity of the chain; returns True if valid."""
        return self.is_valid()

    def create_genesis_block(self) -> Block:
        """Create and return the genesis block (first block in the chain)."""
        blok = Block("0", "0")
        blok.close_block()
        blok.header["hash"] = "0"
        return blok

    def create_block_data_hash(self, data: List[str]) -> str:
        """Compute a SHA-256 hash from a list of string data items."""
        hasher = hashlib.sha256()
        [hasher.update(f"{item}".encode('utf-8')) for item in data]
        return hasher.hexdigest()

    def add_new_block(self, new_block: Block) -> None:
        """Append a new block to the chain, linking it to the previous block via hashes."""
        new_block.header["prev_hash"] = self.chain[-1].header["hash"]
        new_block.header["hash"] = self.create_block_data_hash(
            [new_block.header["prev_hash"], new_block.header["data_hash"]])
        self.chain.append(new_block)
        self.refresh_block()

    def get_last_block(self) -> Block:
        """Return the most recent block in the chain."""
        return self.chain[-1]

    def get_hashes(self) -> List[Tuple[str, str]]:
        """Return a list of (hash, prev_hash) tuples for every block."""
        return [(block.header["hash"], block.header["prev_hash"]) for block in self.chain]

    def add_transaction_to_block(self, unsaved_block):
        pass

    def is_valid(self) -> bool:
        """Verify the integrity of the entire chain (hash linkage and content hashes)."""
        for i, blck in enumerate(self.chain):
            if i == 0:
                continue
            prev_blck = self.chain[i - 1]

            if prev_blck.header["hash"] != blck.header["prev_hash"]:
                return False

            expected_hash = self.create_block_data_hash(
                [blck.header["prev_hash"], blck.header["data_hash"]])
            if blck.header["hash"] != expected_hash:
                return False
        return True

    def get_block(self, block_hash: str) -> List[Block]:
        """Return all blocks matching the given block hash."""
        return [block for block in self.chain
                if block.header["hash"] == block_hash]

    def delete_all_blocks(self):
        pass


@dataclass
class HashChain:
    """A set-based collection of HashBlocks for lightweight chain comparison."""

    chain: set | None = None

    def __post_init__(self):
        if self.chain is None:
            self.chain = set()

    def add_block(self, block: HashBlock) -> None:
        """Add a HashBlock to the chain set."""
        self.chain.add(block)

    def find_block(self, block: str) -> int:
        """Return the count of blocks matching the given hash string."""
        return self.chain.count(block)

    def find_transactions(self, transaction: str, user: str):
        pass

    def get_subset(self, o_chain) -> bool:
        """Return True if o_chain's blocks are a subset of this chain's blocks."""
        return set(o_chain.chain).issubset(set(self.chain))

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return len(self.chain) <= len(other.chain)

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return len(self.chain) < len(other.chain)
