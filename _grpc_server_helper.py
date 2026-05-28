"""gRPC server for node-to-node block synchronization."""
import json
from dataclasses import asdict
from typing import Any, List

import grpc

import block_pb2
import block_pb2_grpc
from blockchain.block import Block as ChainBlock
from blockchain.blockchain import Chain
from blockchain.transaction import Transaction
from block_pb2 import Block


class BlockDownloader(block_pb2_grpc.BlockDownloaderServicer):
    """gRPC servicer that streams blocks and hash metadata to requesting peers."""

    def __init__(self, chain: Chain):
        super(BlockDownloader, self).__init__()
        self.chain = chain

    def get_block_range(self, chain: Chain, block_id: str) -> List[ChainBlock]:
        """Return all blocks from the block matching block_id to the end of the chain.

        Args:
            chain: The blockchain instance.
            block_id: The hash of the starting block.

        Returns:
            List of Block objects from the matching block onward.
        """
        block_0_range = self.chain.get_block(block_id)[0]
        return self.chain.chain[self.chain.chain.index(block_0_range):]

    def DownloadBlocks(self, request: Any, context: Any) -> Block:
        """Stream all blocks from the requested hash to the end of the chain.

        Yields:
            Block protobuf messages.
        """
        blocks_2send = self.get_block_range(self.chain, request.hash)
        for block in blocks_2send:
            tx_dicts = [asdict(tx) for tx in block.transactions]
            yield Block(header=json.dumps(block.header),
                        transactions=json.dumps(tx_dicts))

    def GetHashBlocks(self, request: Any, context: Any) -> block_pb2.HashBlock:
        """Stream HashBlock metadata from the requested hash to the end of the chain.

        Yields:
            HashBlock protobuf messages.
        """
        blocks_2send = self.get_block_range(self.chain, request.hash)
        for block in blocks_2send:
            yield block_pb2.HashBlock(
                hash=str(block.header['hash']),
                data_hash=str(block.header['data_hash']),
                prev_hash=str(block.header['prev_hash']))

    def DownloadBlock(self, request: Any, context: Any) -> block_pb2.BlockResponse:
        """Return a single block by its hash ID.

        Args:
            request: BlockRequest with the block hash.
            context: gRPC context.

        Returns:
            BlockResponse containing the requested block.
        """
        print(f"Looking for block with id : {request.id}")
        block = self.chain.get_block(request.id)
        return block_pb2.BlockResponse(
            block=Block(
                header=str(block[0].header),
                transactions=str([block[0].transactions])))


