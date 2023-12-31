
import hashlib
import cryptography
from BlockChain import create_hash
from .Security import verify_data, encrypt_data


class Transaction:

    def __init__(self, _type, data, metadata):
        self.type = _type
        self.data = data  # transaction data
        self.metadata = metadata
        self.hash = create_hash(self.data)

    def verified(self):
        return verify_data(self.data, self.metadata['signature'], self.metadata['pk'])
