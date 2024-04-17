# node-to-node communication through Google`s GRPC
# contain all the methods and classes for running the grpc client

from __future__ import print_function
import sys
import time
import grpc
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import block_pb2
import block_pb2_grpc
from blockchain.block import Block, HashBlock
from blockchain.storage.onchain import save_transaction
from blockchain.trasanction import HashTransaction, Transaction
from blockchain.blockchain import HashChain, Chain
from blockchain.peer import Peer


node_peers = None
database = None


def download_peer_block(peer_address, block_id):
    print(f"Downloading chain from {peer_address}")
    with grpc.insecure_channel(peer_address) as channel:
        stub = block_pb2_grpc.BlockDownloaderStub(channel)
        response = stub.DownloadBlock(block_pb2.BlockRequest(id=block_id))
        print(f"Block from server : {response}")  # return block

def download_peer_blocks(peer_address, chain, block_id, database=None):
    with grpc.insecure_channel(f"{peer_address}:50051") as channel:
        stub = block_pb2_grpc.BlockDownloaderStub(channel)
        
        for block in stub.DownloadBlocks(
                block_pb2.BlocksRequest(hash=str(block_id))):
            block_header = eval(block.header)
            
            print(f"block block : {block}")
            
            # ignore the first block
            if block_header["hash"] == "0" and len(chain.chain) == 1:
                continue
            
            expected_prev_block = block_header["prev_hash"]
            expected_data_hash = block_header["data_hash"]
            
            block_transactions = eval(block.transactions)

            for transaction in block_transactions:
                save_transaction(database, transaction)
            
            blk = Block()
            
            blk.header["prev_hash"] = chain.get_last_block().header["hash"]
            blk.header["hash"] = block_header["hash"]
            # block prev hash must match expected prev hash
            if expected_prev_block != blk.header["prev_hash"]:
                # wrong blocks
                # chain.delete_all_blocks()
                print("Block hash mismatch while downloading!!")
                print(f"Expected :  {expected_prev_block} : "
                      f"found : {blk.header['prev_hash']}")
                print(f"Ignoring block : {blk.header}")
                continue
            
            blk.transactions = [x for x in block_transactions
                                if isinstance(x, Transaction)]
            blk.close_block()
            
            if expected_data_hash != blk.header["data_hash"]:
                # transactions do not match hash
                # transactions may have been altered
                
                # global node_peers, database

                chain_validator = ChainValidator(node_peers, Chain(), database)
                chain_validator.corrupted_peers.add(peer_address)
                chain_validator.get_all_chains_tp()

                print("Transaction integrity check failed while downloading!!")
                continue
            if database.save_block(blk):
                chain.add_new_block(blk)

            
        
    return   # done downloading the blocks to my chain


class ChainValidator:
    
    def __init__(self, peers, chain, database):
        self.peers = peers  # a set of peers
        self.chains_to_validate = {}
        self.chain = chain
        self.last_block_hash = chain.get_last_block().header["hash"]
        self.database = database
        self.corrupted_peers = set() # addresses

        # global node_peers, database
        node_peers = self.peers
        database = self.database
        
        print("Initializing chain validator")
        if len(self.peers) < 1:
            print("All Peers corrupt")
            return
        
    def get_chain_sizes(self):
        pass
    
    def download_chain(self, peer):
        hash_chain = HashChain(chain=set())
        print(f"Downloading from : {peer.address[0]}:50051")

        with grpc.insecure_channel(f"{peer.address[0]}:50051") as channel:
            stub = block_pb2_grpc.BlockDownloaderStub(channel)
            
            for block in stub.GetHashBlocks(
                    block_pb2.HashBlocksRequest(hash=str(self.last_block_hash))):
                print(f"hash block downloaded {block}")
                hash_chain.add_block(HashBlock(hash=block.hash,
                    previous_hash=block.prev_hash,data_hash=block.data_hash))
        return hash_chain
    
    def valida_chains(lg_chain, other_chains):
        pass
    
    def get_all_chains_tp(self):
        print(f"staring threadpool executor : {len(self.peers)}")

        self.peers = [peer for peer in self.peers if
                      not self.corrupted_peers.__contains__(peer)]
            # TODO fix address issue

        with ThreadPoolExecutor(max_workers=len(self.peers)) as executor:
            future_to_chain = {
                executor.submit(self.download_chain, peer): 
                    peer for peer in self.peers}
            
            for future in as_completed(future_to_chain):
                peer = future_to_chain[future]
                try:
                    data = future.result()
                    self.chains_to_validate[peer] = data
                except Exception as ex:
                    print("TP GRPC Error : ", ex)
        
        lg_chain = list(self.chains_to_validate.values())[0]
        lg_node = list(self.chains_to_validate.keys())[0]
        
        for peer, chain in self.chains_to_validate.items():
            print(f"{peer} : {chain}")
            if chain >= lg_chain:
                lg_chain = chain
                lg_node = peer
        
        smaller_chains = [chain for chain 
            in list(self.chains_to_validate.values()) 
            if chain < lg_chain]
        
        print(f"Smaller chains : {smaller_chains}")
        
        subset = 0
        for s_chain in smaller_chains:
            if lg_chain.get_subset(s_chain):
                subset += 1
        
        print(f"{subset / len(list(self.chains_to_validate.values())) :.2f} "
              f"% agree with largest chain")
        
        if subset / len(list(self.chains_to_validate.values())) >= 0.5:
            # smaller chains are part of the larger chain
            print(f"Largest node : {lg_node} with {lg_chain}")
            download_peer_blocks(f"{lg_node.address[0]}",
                self.chain, self.chain.get_last_block().header['hash'],
                self.database)

        elif (subset / len(list(self.chains_to_validate.values())) == 0
              and len(self.peers) == 1):
            
            print(f"One node : {lg_node} with {lg_chain}")
            download_peer_blocks(f"{lg_node.address[0]}",
                self.chain, self.chain.get_last_block().header['hash'],
                self.database)
        else:
            print(f"no peer agree still downloading")
            # reject the larger chain and go for a smaller chain
            download_peer_blocks(f"{lg_node.address[0]}", self.chain,
                self.chain.get_last_block().header['hash'], self.database)
            # self.peers.pop(lg_node)
            # self.get_all_chains_tp()  # repeat the process
        return

