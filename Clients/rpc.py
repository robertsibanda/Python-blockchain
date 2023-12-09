from jsonrpcserver import method, Success, Error, response, request
import time
from BlockChain import BlockChain
from .decorators import authenticated


@authenticated
def is_chain_valid(chain, headers):
    return chain.valid_chain()


@authenticated
def hello(name, age, headers):
    return Success('{} is {} years old'.format(name, age))


@authenticated
def new_patient(details):
    return Success("patient added")


@authenticated
def add_record(details):
    return Success("record added")


@authenticated
def get_block(block_id, chain):
    for block in chain:
        if block.hash == block_id:
            return Success(block)


@authenticated
def add_record(record):
    pass
