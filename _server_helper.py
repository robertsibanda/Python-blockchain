
import grpc
from concurrent import futures
from twisted.internet import reactor
import datetime

import block_pb2_grpc
from _grpc_client_helper import ChainValidator
from _grpc_server_helper import BlockDownloader

import blockchain.blockchain
from blockchain.blockchain import Chain
from blockchain.peer import Peer
from blockchain.block import Block

def process_peer_chain_request(chain: blockchain.blockchain.Chain):
    return [block.header['hash'] for block in chain.chain]


def process_close_block(transaction_queue, transactions):
    
    block_tx = []

    for tx in transactions:
        for t in transaction_queue:
            if t.hash == tx:
                block_tx.append(t)

    for tx in transaction_queue:
        print(f"Transaction from queue: {tx.hash}")

    tx_toadd = [tx for tx in transaction_queue if tx.hash in transactions]

    print(f"tx_toadd : {tx_toadd}")
    
    for tx in tx_toadd:
        for t in transaction_queue:
            if tx is t:
                transaction_queue.remove(t)
    
    print(f"Transaction Queue after adding {[tx.hash for tx in transaction_queue]}")

    if len(tx_toadd) == len(transactions):
        return {"transactions": tx_toadd, "found": True}
    
    else:
        return { "found" : False}


def new_node_regiser(new_node_props: dict, chain: Chain, peer: Peer,
                     chains_to_validate: dict):
    
    my_chain_props = {
        "chain-length": str(len(chain.chain)),
        "last-block": chain.get_last_block().header['hash']}

    if new_node_props[1] == my_chain_props:
        return {"response": "chains-equal"}

    if new_node_props != my_chain_props:
        if my_chain_props["chain-length"] > new_node_props[1]["chain-length"]:
            # my chains is greater than requester
            return {"response": "-chain"}

        if my_chain_props["chain-length"] < new_node_props[1]["chain-length"]:
            # my chain smaller that requester
            # TODO work on copying chain
            return {"response": "+chain"}
        
        if my_chain_props["last-block"] != new_node_props[1]["last-block"]:
            # chains are equal but hashes do not match
            return {"response": "^hash"}
    


def grpc_server(chain):
    # the grpc server for downloading chain from other nodes
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    block_pb2_grpc.add_BlockDownloaderServicer_to_server(BlockDownloader(chain), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


def twisted_server(server):
    # all nodes must not use port 9009 -> its for node-list-server
    port = 5000
    reactor.listenUDP(port, server)
    reactor.run()


