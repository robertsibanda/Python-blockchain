from __future__ import print_function
import grpc
import block_pb2
import block_pb2_grpc


def download_peer_block(peer_address, block_id):
    with grpc.insecure_channel(peer_address) as channel:
        stub = block_pb2_grpc.BlockDownloaderStub(channel)
        response = stub.DownloadBlock(block_pb2.BlockRequest(id=block_id))
        print(f"Block from server : {response}")  # return block


def download_peer_blocks(peer_address, block_id):
    with grpc.insecure_channel(peer_address) as channel:
        stub = block_pb2_grpc.BlockDownloaderStub(channel)
        for block in stub.DownloadBlocks(block_pb2.BlocksRequest(startingBlock=block_id)):
            # save the blocks to chain after validating
            print(f"Block recieved : {block.transactions}")
        return  # done downloading the blocks to my chain


def validate_peer_block(peer_address):
    return