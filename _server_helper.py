import blockchain.blockchain
from blockchain.blockchain import Chain
from blockchain.peer import Peer
import grpc
from concurrent import futures
from twisted.internet import reactor
import block_pb2_grpc
from _grpc_client_helper import ChainValidator
from _grpc_server_helper import BlockDownloader

def process_peer_chain_request(chain: blockchain.blockchain.Chain):
    return [block.header['hash'] for block in chain.chain]


def process_close_block(transaction_queue: list, transactions):
    
    # check if you have all the data needed to create the block
    transaction_hashes = [tr.hash for tr in transaction_queue]
    found_hash = [tr in transaction_hashes for tr in transactions]
    
    new_block_transactions = []
    
    if found_hash.count(False) > 0:
        # some transactions not found
        # request from other nodes
        return {"found": False}
    
    for tr in transaction_queue:
        for tr2 in transaction_hashes:
            if tr == tr2:
                new_block_transactions.append(tr)
                transaction_queue.remove(tr)
                
    return {"transactions": new_block_transactions, "found": True}


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

    
