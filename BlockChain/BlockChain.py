import random
import hashlib
import time
import pymongo
from Block import Block
import sys


# commented
class Chain:

    def __init__(self, chain):
        self.chain = [self.create_genesis_block()]

    def refresh_block(self):
        if self.valid_block():
            print('Block Valid')
        else:
            sys.exit(1)

    def create_genesis_block(self):
        blok = Block(0, 'Genesis Block')
        blok.hash = self.create_hash(blok.data)
        return blok

    def add_new_block(self, new_block: Block):
        new_block.prev_hash = self.chain[-1].hash
        new_block.hash = self.create_hash(new_block.data)
        self.chain.append(new_block)
        self.refresh_block()

    def get_last_block(self):
        return self.chain[-1]

    def create_hash(self, data):
        return hashlib.sha256('{}'.format(data).encode('ascii')).hexdigest()

    def valid_block(self):
        for blck in self.chain:
            if self.chain.index(blck) == 0:
                continue

            if self.chain[self.chain.index(blck) - 1].hash != blck.prev_hash:
                return False

            if blck.hash != self.create_hash(blck.data):
                return False
        return True
