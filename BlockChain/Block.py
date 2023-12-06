# Robert Sibanda (robertsibanda20@gmail.com)
# .
import hashlib
import cryptography

from .BlockChain import create_hash

create_hash('as')

class Block:

    def __init__(self, _hash='', prev_hash='', transactions=[]):
        self.transactions = transactions  # transactions
        self.header = {
            'hash': _hash,
            'prev_hash': prev_hash,
            'data_hash': None
        }

        transactionHashes = []
        for transaction in self.transactions:
            transactionHashes.append(transaction.hash)

        self.header['data_hash'] = create_hash(transactionHashes)
