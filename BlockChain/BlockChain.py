# Robert Sibanda (robertsibanda20@gmail.com)
# .

import hashlib
import sys
from . import Block


# commented
def create_hash(data):
    return hashlib.sha256('{}'.format(data).encode('ascii')).hexdigest()


class Chain:

    def __init__(self, chain):
        """
        initilize chain with genesis block, staring point of chain
        """
        self.chain = [self.create_genesis_block()]

    def refresh_block(self) -> bool:
        """
        check the valdity of the chain periodically
        or when adding new block depending on what you prefer
        """
        if self.valid_chain():
            return True
        return False

    def create_genesis_block(self) -> Block:
        blok = Block.Block(0, 'Genesis Block')
        blok.hash = create_hash(blok.transactions)
        return blok

    def add_new_block(self, new_block: Block):
        """
        new block is added ,
        hash calculated using hashlib 'https://hashlib.com'
        linked with previous block`s hash
        """
        new_block.header["prev_hash"] = self.chain[-1].header["hash"]
        new_block.header["hash"] = create_hash(new_block.transactions)
        self.chain.append(new_block)
        self.refresh_block()

    def get_last_block(self) -> Block:
        """last block os the chain """
        return self.chain[-1]

    def get_hashes(self):
        return [(block.hash, block.prev_hash) for block in self.chain]

    def add_transaction_to_block(self, unsaved_block):
        pass

    def valid_chain(self) -> bool:
        """check validity of the chian"""
        for blck in self.chain:
            if self.chain.index(blck) == 0:
                """ignore the first block"""
                continue

            if self.chain[self.chain.index(blck) - 1].header["hash"] != blck.header["prev_hash"]:
                """chech the link between adjuscent blocks"""
                return False

            if blck.header["hash"] != create_hash(blck.transactions):
                """check the validity of a block`s hash based on data contents"""
                return False
        return True
