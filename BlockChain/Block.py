# Robert Sibanda (robertsibanda20@gmail.com)
# .
import hashlib

from .BlockChain import create_hash

MAX_TRANSACTIONS = 2  # max number of transactions in a block


class Block:
    
    def __init__(self, _hash='', prev_hash='', transactions=None):
        if transactions is None:
            transactions = []
        self.transactions = transactions  # transactions
        self.header = {'hash': _hash, 'prev_hash': prev_hash, 'data_hash': ''
                       }
    
    def add_new_transaction(self, transaction) -> bool:
        print(f"Adding new transaction in length of {len(self.transactions)}")
        if len(self.transactions) == MAX_TRANSACTIONS:
            self.close_block()
            print("Added new block to chain")
            return False
        self.transactions.append(transaction)
        print("Added transaction :  ", transaction.hash)
        return True
    
    def create_block_data_hash(self, data):
        hasher = hashlib.sha256()
        [hasher.update(item.encode('utf-8')) for item in data]
        self.header['data_hash'] = hasher.hexdigest()
        return
    
    def close_block(self):
        transaction_hashes = []
        for transaction in self.transactions:
            transaction_hashes.append(transaction.hash)
        self.create_block_data_hash(transaction_hashes)
        return
