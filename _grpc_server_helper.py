# node 2 node communication through googleRPC
# contain all the methods and classes for running the grpc server
from concurrent import futures

import grpc
from pymongo import MongoClient

import block_pb2
import block_pb2_grpc
from blockchain.blockchain import Chain
from blockchain.trasanction import Transaction
from block_pb2 import Block

# TODO make all commuications singed and encrypted


class BlockDownloader(block_pb2_grpc.BlockDownloaderServicer):
    
    def __init__(self, chain):
        super(BlockDownloader, self).__init__()
        self.chain = chain
    
    def get_block_range(self, chain, block_id):
        block_0_range = self.chain.get_block(block_id)[0]
        
        blocks_2send = self.chain.chain[self.chain.chain.index(block_0_range):]
        return blocks_2send
    
    def DownloadBlocks(self, request, context):
        print(f"Download request id : {request.hash}")

        blocks_2send = self.get_block_range(self.chain, request.hash)

        print("Sending blocks")
        
        for block in blocks_2send:
            print('Sending Block : ' ,  block.header)
            yield Block(header=str(block.header),
                        transactions=str(block.transactions))
        print("done sending blocks")
    
    def GetHashBlocks(self, request, context):
        
        blocks_2send = self.get_block_range(self.chain, request.hash)
    
        for block in blocks_2send:
            print(block.header)
            yield block_pb2.HashBlock(hash=str(block.header['hash']),
                                      data_hash=str(block.header['data_hash']),
                                      prev_hash=str(block.header['prev_hash']))
            print("Done sending hash blockss")
            
    def DownloadBlock(self, request, context):
        print(f"Looking for block with id : {request.id}")
        block = self.chain.get_block(request.id)
        return block_pb2.BlockResponse(
            block=Block(
                header=str(block[0].header),
                transactions=str([block[0].transactions])))


