# Robert Sibanda (robertsibanda20@gmail.com)
# .

import hashlib
from BlockChain.Block import Block
import sys


# commented
def create_hash(data):
    return hashlib.sha256('{}'.format(data).encode('ascii')).hexdigest()


class Chain:

    def __init__(self, chain):
        """
        initilize chain with genesis block, staring point of chain
        """
        self.chain = [self.create_genesis_block()]

    def refresh_block(self):

        """
        check the valdity of the chain periodically
        or when adding new block depending on what you prefer
        """
        if self.valid_block():
            return True
        return False

    def create_genesis_block(self):
        blok = Block(0, 'Genesis Block')
        blok.hash = create_hash(blok.data)
        return blok

    def add_new_block(self, new_block: Block):
        """
        new block is added ,
        hash calculated using hashlib 'https://hashlib.com'
        linked with previous block`s hash
        """
        new_block.prev_hash = self.chain[-1].hash
        new_block.hash = create_hash(new_block.data)
        self.chain.append(new_block)
        self.refresh_block()

    def get_last_block(self):
        """last block os the chain """
        return self.chain[-1]

    def valid_block(self):
        """check validity of the chian"""
        for blck in self.chain:
            if self.chain.index(blck) == 0:
                """ignore the first block"""
                continue

            if self.chain[self.chain.index(blck) - 1].hash != blck.prev_hash:
                """chech the link between adjuscent blocks"""
                return False

            if blck.hash != create_hash(blck.data):
                """check the validity of a block`s hash based on data contents"""
                return False
        return True
