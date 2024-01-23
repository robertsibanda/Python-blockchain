# contains all other methods for blockchain
from . import block
from . import blockchain
from . import peer
import hashlib


def load_from_database() -> blockchain.Chain:
    """Load blockchain from exiting mongo database"""
    chain = blockchain.Chain()
    return chain


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


def lookup_transactions(chain: blockchain.Chain) -> []:
    """
    takes a little while to lookup all transactions
    """
    pass
