# contains all other methods for blockchain
from . import Block
from . import BlockChain
from . import Peer


def create_new_block(transction_data):
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
