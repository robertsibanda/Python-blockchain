"""Server helper utilities for gRPC, Twisted, and node registration logic."""
import grpc
from concurrent import futures
from twisted.internet import reactor
from typing import Any, Dict, List

import block_pb2_grpc
from _grpc_server_helper import BlockDownloader

import blockchain.blockchain
from blockchain.blockchain import Chain
from blockchain.peer import Peer
from blockchain.block import Block


def process_peer_chain_request(chain: blockchain.blockchain.Chain) -> List[str]:
    """Return a list of block hashes for the given chain.

    Args:
        chain: The blockchain instance.

    Returns:
        List of block header hashes.
    """
    return [block.header['hash'] for block in chain.chain]


def process_close_block(transaction_queue: List[Any], transactions: List[str]) -> Dict[str, Any]:
    """Match and remove confirmed transactions from the queue for block finalization.

    Args:
        transaction_queue: List of pending transactions.
        transactions: List of transaction hash strings to confirm.

    Returns:
        Dict with keys 'transactions' (list of matched Transaction objects) and 'found' (bool).
    """
    tx_toadd = [tx for tx in transaction_queue if tx.hash in transactions]

    for tx in tx_toadd:
        for t in transaction_queue:
            if tx is t:
                transaction_queue.remove(t)

    if len(tx_toadd) == len(transactions):
        return {"transactions": tx_toadd, "found": True}
    else:
        return {"found": False}


def new_node_register(new_node_props: list, chain: Chain,
                      transport: Any, signing_peer: Peer) -> Dict[str, str]:
    """Compare a new node's chain properties with the local chain and return a response.

    Args:
        new_node_props: List containing [message_label, {chain-length, last-block}].
        chain: The local blockchain.
        transport: The UDP transport for sending messages.
        signing_peer: The peer requesting registration.

    Returns:
        Dict with a 'response' key indicating chain comparison result.
    """
    my_chain_props = {
        "chain-length": str(len(chain.chain)),
        "last-block": chain.get_last_block().header['hash']
    }

    if new_node_props[1] == my_chain_props:
        return {"response": "chains-equal"}

    if new_node_props != my_chain_props:
        if my_chain_props["chain-length"] > new_node_props[1]["chain-length"]:
            return {"response": "-chain"}

        if my_chain_props["chain-length"] < new_node_props[1]["chain-length"]:
            return {"response": "+chain"}

        if my_chain_props["last-block"] != new_node_props[1]["last-block"]:
            return {"response": "^hash"}

    return {"response": "chains-equal"}


def grpc_server(chain: Chain) -> None:
    """Start the gRPC server for block synchronization between nodes.

    Args:
        chain: The blockchain instance to serve.
    """
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    block_pb2_grpc.add_BlockDownloaderServicer_to_server(BlockDownloader(chain), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


def twisted_server(server: Any) -> None:
    """Start the Twisted UDP server for peer-to-peer messaging.

    Args:
        server: A DatagramProtocol instance.
    """
    port = 5000
    reactor.listenUDP(port, server)
    reactor.run()


