# node-to-node communication through Google`s GRPC
# contain all the methods and classes for running the grpc client

from __future__ import print_function
import sys
import time
import grpc
import threading

import block_pb2
import block_pb2_grpc
from blockchain.block import Block, HashBlock
from blockchain.trasanction import HashTransaction, Transaction
from blockchain.blockchain import HashChain


# TODO make all commuications singed and encrypted

def download_peer_block(peer_address, block_id):
    with grpc.insecure_channel(peer_address) as channel:
        stub = block_pb2_grpc.BlockDownloaderStub(channel)
        response = stub.DownloadBlock(block_pb2.BlockRequest(id=block_id))
        print(f"Block from server : {response}")  # return block


def download_peer_blocks(peer_address, chain, block_id, database=None):
    with grpc.insecure_channel(f"{peer_address}:50051") as channel:
        stub = block_pb2_grpc.BlockDownloaderStub(channel)
        
        for block in stub.DownloadBlocks(block_pb2.BlocksRequest(string_block=block_id)):
            block_header = eval(block.header)
            
            # ignore the first block
            if block_header["hash"] == 0 and len(chain.chain) == 1:
                continue
            
            expected_prev_block = block_header["prev_hash"]
            expected_data_hash = block_header["data_hash"]
            
            block_transactions = eval(block.transactions)
            
            blk = Block()
            
            blk.header["prev_hash"] = chain.get_last_block().header["hash"]
            blk.header["hash"] = block_header["hash"]
            # block prev hash must match expected prev hash
            if expected_prev_block != blk.header["prev_hash"]:
                # wrong blocks
                chain.delete_all_blocks()
                print("Block hash mismatch while downloading!!")
                print(f"Expected :  {expected_prev_block} : "
                      f"found : {blk.header['prev_hash']}"
                      )
                sys.exit()
            
            blk.transactions = [x for x in block_transactions
                                if isinstance(x, Transaction)]
            blk.close_block()
            
            if expected_data_hash != blk.header["data_hash"]:
                # transactions do not match hash
                # transactions may have been altered
                # TODO create a way to counter modified transactions
                print("Transaction integrity check faile while downloading!!")
                sys.exit()
            
            database.save_block(blk)
            chain.add_new_block(blk)
        
        return  # done downloading the blocks to my chain


class ChainValidator:
    
    # TODO re-do this class for cleaner code -> last-block can be found on chain
    
    def __init__(self, peers, last_block, chain, database):
        self.peers = peers  # a set of peers
        self.last_block = last_block  # last block on my chain
        self.largest_valid_peer_chain = None
        self.larget_valid_peer_node = None
        self.larget_valid_block_hash = None
        self.chains_to_validate = {}
        self.magority_downloaded = False
        self.chain = chain
        self.database = database
    
    def get_chain_sizes(self):
        pass
    
    def download_chain(self, peer):
        hash_chain = HashChain()
        with grpc.insecure_channel(peer.address) as channel:
            stub = block_pb2_grpc.BlockDownloaderStub(channel)
            for block in stub.GetHashBlocks(block_pb2.HashBlocksRequest(hash="")):
                hash_chain.add_block(block)
            self.chains_to_validate[peer.name] = hash_chain
    
    def download_monitor(self):
        # TODO replace monitor thread with async::await
        # monitor if all threads have finished downloading
        # TODO replace this method with multiple smaller methods

        thread_names_to_stop = [peer.name for peer in self.peers]
        time_count = 0
        
        while [x in [thread.name for thread in threading.enumerate()]
               for x in thread_names_to_stop]:
            # threads are still downloading block-hashes-chain
            time_count += 1
            time.sleep(1)
            
        lg_chain = list(self.chains_to_validate.values())[0]
        lg_node = list(self.chains_to_validate.keys())[0]
        
        for peer, chain in self.chains_to_validate.items():
            if chain > lg_chain:
                lg_chain = chain
                lg_node = peer
        
        smaller_chains = [chain for chain in list(self.chains_to_validate.values())
                          if chain < lg_chain]
        
        subset = 0
        for s_chain in smaller_chains:
            if lg_chain.get_subset(s_chain):
                subset += 1
        
        if subset / len(list(self.chains_to_validate.values())) >= 0.5:
            # smaller chains are part of the larger chain
            download_peer_blocks(lg_node.address, self.chain,
                                 self.chain.get_last_block(), self.database)
        else:
            # reject the larger chain and go for a smaller chain
            self.peers.pop(lg_node)
            # TODO replace redownload with re-validation
            self.get_all_chains()  # repeat the process
        return
        
    def get_all_chains(self):
        monitor_thread = threading.Thread(target=self.download_monitor())
        monitor_thread.start()
        
        for peer in self.peers:
            th = threading.Thread(target=self.download_chain(peer))
            th.name = peer.name
            th.start()
            th.join()
