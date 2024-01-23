# node 2 node communication through googleRPC
# contain all the methods and classes for running the grpc server

from pymongo import MongoClient

import block_pb2
import block_pb2_grpc
from blockchain.trasanction import Transaction
from block_pb2 import Block

# TODO make all commuications singed and encrypted


class BlockDownloader(block_pb2_grpc.BlockDownloaderServicer):
    
    def __init__(self, chain):
        super(BlockDownloader, self).__init__()
        self.chain = chain
    
    def DownloadBlocks(self, request, context):
        print(f"Download request id : {request.string_block} : {request}")
        
        if request.string_block == "0" or 0:
            block_0_range = self.chain.get_block(int(request.string_block))[0]
        else:
            block_0_range = self.chain.get_block(request.string_block)[0]
        
        blocks_2send = self.chain.chain[self.chain.chain.index(block_0_range):]
            
        for block in blocks_2send:
            print(block.header)
            yield Block(header=str(block.header),
                        transactions=str(block.transactions)
                        )
              
    def DownloadBlock(self, request, context):
        print(f"Looking for block with id : {request.id}")
        block = self.chain.get_block(request.id)
        return block_pb2.BlockResponse(
            block=Block(
                header=str(block[0].header),
                transactions=str([block[0].transactions])))
