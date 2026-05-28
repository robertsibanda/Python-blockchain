"""gRPC client helpers for peer-to-peer block synchronization."""
from __future__ import print_function
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set

import grpc

import block_pb2
import block_pb2_grpc
from blockchain.block import Block, HashBlock
from blockchain.blockchain import Chain, HashChain
from blockchain.peer import Peer
from blockchain.storage.onchain import save_transaction
from blockchain.transaction import Transaction


node_peers: Optional[Set[Peer]] = None
database: Optional[Any] = None


def download_peer_block(peer_address: str, block_id: str) -> None:
    """Download a single block from a peer via gRPC.

    Args:
        peer_address: The peer's address (host:port).
        block_id: The block hash to download.
    """
    with grpc.insecure_channel(peer_address) as channel:
        stub = block_pb2_grpc.BlockDownloaderStub(channel)
        stub.DownloadBlock(block_pb2.BlockRequest(id=block_id))


def download_peer_blocks(peer_address: str, chain: Chain, block_id: str,
                         database: Optional[Any] = None) -> None:
    """Download all blocks from a peer starting at the given block hash.

    Args:
        peer_address: The peer's host address.
        chain: The local chain to append blocks to.
        block_id: The starting block hash.
        database: Optional database instance for persisting transactions.
    """
    with grpc.insecure_channel(f"{peer_address}:50051") as channel:
        stub = block_pb2_grpc.BlockDownloaderStub(channel)

        for block in stub.DownloadBlocks(
                block_pb2.BlocksRequest(hash=str(block_id))):
            block_header = json.loads(block.header)
            if block_header["hash"] == "0" and len(chain.chain) == 1:
                continue

            expected_prev_block = block_header["prev_hash"]
            expected_data_hash = block_header["data_hash"]

            block_transactions_dicts = json.loads(block.transactions)
            block_transactions = [Transaction(**tx) for tx in block_transactions_dicts]

            for transaction in block_transactions:
                save_transaction(database, transaction)

            blk = Block()
            blk.header["prev_hash"] = chain.get_last_block().header["hash"]
            blk.header["hash"] = block_header["hash"]
            if expected_prev_block != blk.header["prev_hash"]:
                continue
            blk.transactions = [x for x in block_transactions if isinstance(x, Transaction)]
            blk.close_block()

            if expected_data_hash != blk.header["data_hash"]:
                chain_validator = ChainValidator(node_peers, Chain(), database)
                chain_validator.corrupted_peers.add(peer_address)
                chain_validator.get_all_chains_tp()
                print("Transaction integrity check failed while downloading!!")
                continue
            if database.save_block(blk):
                chain.add_new_block(blk)


class ChainValidator:
    """Validates chains from multiple peers and downloads the most agreed-upon chain."""

    def __init__(self, peers: Set[Peer], chain: Chain, db: Any):
        global node_peers
        self.peers: Set[Peer] = peers
        self.chains_to_validate: Dict[Peer, HashChain] = {}
        self.chain = chain
        self.last_block_hash = chain.get_last_block().header["hash"]
        self.database = db
        self.corrupted_peers: Set[str] = set()

        node_peers = self.peers
        globals()['database'] = self.database

        if len(self.peers) < 1:
            print("All Peers corrupt")

    def get_chain_sizes(self) -> None:
        """Placeholder: collect chain sizes from peers."""
        pass

    def download_chain(self, peer: Peer) -> HashChain:
        """Download hash-chain metadata from a peer via gRPC.

        Args:
            peer: The peer to download from.

        Returns:
            A HashChain containing the peer's block hashes.
        """
        hash_chain = HashChain()
        with grpc.insecure_channel(f"{peer.address[0]}:50051") as channel:
            stub = block_pb2_grpc.BlockDownloaderStub(channel)
            for block in stub.GetHashBlocks(
                    block_pb2.HashBlocksRequest(hash=str(self.last_block_hash))):
                hash_chain.add_block(HashBlock(
                    hash=block.hash, prev_hash=block.prev_hash, data_hash=block.data_hash))
        return hash_chain

    def valida_chains(self, lg_chain: HashChain, other_chains: List[HashChain]) -> None:
        """Placeholder: validate chains against the largest chain."""
        pass

    def get_all_chains_tp(self) -> None:
        """Download hash chains from all peers using thread pool and select the most valid."""
        self.peers = {peer for peer in self.peers
                      if peer not in self.corrupted_peers}

        with ThreadPoolExecutor(max_workers=len(self.peers)) as executor:
            future_to_chain = {
                executor.submit(self.download_chain, peer): peer
                for peer in self.peers}

            for future in as_completed(future_to_chain):
                peer = future_to_chain[future]
                try:
                    data = future.result()
                    self.chains_to_validate[peer] = data
                except Exception as ex:
                    print("TP GRPC Error : ", ex)

        chains = list(self.chains_to_validate.values())
        nodes = list(self.chains_to_validate.keys())
        if not chains:
            return

        lg_chain = chains[0]
        lg_node = nodes[0]

        for peer, chain in self.chains_to_validate.items():
            if chain >= lg_chain:
                lg_chain = chain
                lg_node = peer

        smaller_chains = [chain for chain in chains if chain < lg_chain]

        subset = 0
        for s_chain in smaller_chains:
            if lg_chain.get_subset(s_chain):
                subset += 1

        total = len(chains)
        agreement = subset / total if total > 0 else 0
        print(f"{agreement:.2f} % agree with largest chain")

        if agreement >= 0.5:
            print(f"Largest node : {lg_node} with {lg_chain}")
            download_peer_blocks(f"{lg_node.address[0]}",
                                self.chain, self.chain.get_last_block().header['hash'],
                                self.database)
        elif agreement == 0 and len(self.peers) == 1:
            print(f"One node : {lg_node} with {lg_chain}")
            download_peer_blocks(f"{lg_node.address[0]}",
                                self.chain, self.chain.get_last_block().header['hash'],
                                self.database)
        else:
            print("no peer agree still downloading")
            download_peer_blocks(f"{lg_node.address[0]}", self.chain,
                                self.chain.get_last_block().header['hash'], self.database)

