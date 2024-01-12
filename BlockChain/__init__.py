# contains all other methods for blockchain
from . import Block
from . import BlockChain
from . import Peer
import hashlib


def load_from_database() -> BlockChain.Chain:
    """Load blockchain from exiting mongo database"""
    chain = BlockChain.Chain()
    return chain


def create_hash_default(data):
    hasher = hashlib.sha256()
    if 'list' in str(type(data)):
        [hasher.update(item.encode('utf-8')) for item in data]
        return hasher.hexdigest()
    return hashlib.sha256(str(data).encode('utf-8')).hexdigest()


def create_new_block(transction_data):
    """
    add new block with first transaction
    :param transction_data: first transaction
    :return: new block id
    """
    pass


def add_transaction(block, transaction):
    pass


def close_block(block):
    pass


def validate_transaction() -> bool:
    pass


def lookup_transactions(chain: BlockChain.Chain) -> []:
    """
    takes a little while to lookup all transactions
    """
    pass
