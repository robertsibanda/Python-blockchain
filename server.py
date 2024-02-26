import sys
import threading
import time
from concurrent import futures
from random import randint

import grpc
import rsa
from jsonrpcserver import serve, method, Success
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

import block_pb2_grpc
from _grpc_client_helper import ChainValidator
from _grpc_server_helper import BlockDownloader
from _server_helper import process_peer_chain_request, new_node_regiser, \
    process_close_block
from blockchain.block import Block
from blockchain.blockchain import Chain
from blockchain.peer import Peer, peer_exists, save_peer
from blockchain.security import verify_data, encrypt_data
from blockchain.security.Identity import Identity
from blockchain.storage.database import Database
from blockchain.trasanction import Transaction
from clients.rpc import register_new_practitioner


database = Database('172.17.0.3', 27017, 'ehr_chain')

chain = Chain()

# load blocks saved before shutdown
database.load_all_blocks(chain)

# load peers connected to before shutdown
database.load_peers()

# check if the chain from database is valid
if chain.is_valid() is not True:
    print("chain invalid XXXX")
    sys.exit()

# create an instance of the identity used to sign and encrypt data
identity = Identity()

# open block for adding new transactions
open_block = Block()

# old block not yet closed
open_block_old = False

# transaction queue of all transactions
transaction_queue = []

# valid and verified transactions
validated_transaction_queue = []


class Server(DatagramProtocol):
    def __init__(self, host, port):
        self.peers = set()
        self.id = '{}:{}'.format(host, port)
        self.address = (host, port)
        self.server = '172.17.0.5', 9009
        self.index_being_validated = 0
        self.new_join = True
        self.chain_leader = False
        self.chain_leader_n = None
        self.chains_to_validate = {}
        print('working on id : ', self.id)
    
    def startProtocol(self):
        """initialize the connection"""
        node_identity = {"status": "ready", "pk": identity.public_key, "name": "node-1"
                         }
        self.transport.write(str(node_identity).encode('utf-8'), self.server)
    
    def datagramReceived(self, datagram: bytes, addr):
        
        if addr[1] == self.server[1]:
            '''
            handle comms comming from node with register of
            online nodes
            '''
            data = datagram.decode().split('->')
        
            if data[1] == '':
                
                print("No peers in the network")
                self.chain_leader = True
                self.new_join = False
                return
            
            if data[0] == 'peers':
                print(f"Data recieved from node-list-srver {data}")
                """
                if node was already running update list of peers
                """
                
                recvd_peers = data[1].split('::::')
                
                new_node = None
                
                for peer in recvd_peers:
                    print('Peer address : ', eval(peer)["address"])
                    if peer_exists(self.peers, peer):
                        continue
                    
                    peer_recvd = eval(peer)
                    
                    save_peer(database, peer_recvd)
                    
                    new_node = Peer(peer_recvd["address"], peer_recvd["public_key"],
                                    peer_recvd["name"])
    
                    self.peers.add(new_node)
                    
                if self.new_join:
                    self.chains_to_validate[new_node.name] = 0
                    """
                    only register and request chain if new node
                    """
                    message = {"chain-length": f"{len(chain.chain)}",
                               "last-block": chain.get_last_block().header["hash"]}
                
                    self.broadcast_message(message, 'register', 0)
                    self.new_join = False
            
            print('\nPeers :{}'.format([f'\t{peer.name}' for peer in self.peers]))
            return
        
        """
        handle comms comming from other peer nodes
        """
        recvd_data = ''
        
        try:
            recvd_data = datagram.decode().split('0000')
        except Exception as excpt:
            print('Failed to decode data : ', excpt)
        try:
            """
            verify data before going forward
            """
            
            # check with key belonging to addr
            signing_peer = None
            verified_data = False
            
            for peer in self.peers:
                if peer.address == addr:
                    signing_peer = peer
            
            # signing_peer = [peer for peer in self.peers if peer.address == addr]
            
            if signing_peer is None:
                # the signing peer is not found using address
                # problem caused by NAT
                # find by bruteforcing the public keys and update the address
                
                print('Peer not found : brute force started')
                
                for peer in self.peers:
                    print(f"Looking at {peer.address} : {peer.name} ")
                    try:
                        verified_data = verify_data(
                            recvd_data[1].encode('utf-8'),
                            eval(recvd_data[0]),
                            rsa.PublicKey.load_pkcs1(peer.pk))
                    except rsa.VerificationError:
                        continue
                    
                    if verified_data:
                        # update the peer address
                        print(f"Peer found updating from {peer.address} to {addr}")
                        peer.address = addr
                        break
                
                if signing_peer is None:
                    # peer not found through brutefore
                    # inform node_list_server
                    return
            
            else:
                print('Signing peer : ', signing_peer.address)
                # print('recieved data : ', recvd_data)
                
                verified_data = verify_data(
                    recvd_data[1].encode('utf-8'),
                    eval(recvd_data[0]),
                    rsa.PublicKey.load_pkcs1(signing_peer.pk))
            
            if verified_data:
                print(f"Data recvd from peer {eval(recvd_data[1])}")
                # print(f"All recieved data : {recvd_data}")
                
                data_request = eval(recvd_data[1])  # recvd_data is list [str, dict]
                # print(f"type of recvd data  : {type(data_request)}")
                
                if data_request[0] == 'register':

                    # dict with properties of the request
                    # {chain-length : x, last-block : y}
                    
                    new_node_chain_props = data_request[1]
                    
                    print(f"New node chain props : {new_node_chain_props}")

                    response = new_node_regiser(
                        new_node_chain_props, chain, self.transport, signing_peer)
                    
                    self.send_message(signing_peer, response, "register-response", 1)
                    
                if data_request[0] == "close-block-request":
                    
                    if signing_peer.name == self.chain_leader:
                        transactions = data_request[1]["transactions"]
                        data_hash = data_request[1]["data_hash"]
                        block_hash = data_request[1]["data_hash"]
                        block_prev_hash = data_request[1]["prev_hash"]
                        
                        # respose { data_hash : '', block_hash : '' }
                        response = process_close_block(transaction_queue, transactions)
                        
                        if response["found"]:
                            new_block = Block()
                            for transaction in response["transactions"]:
                                new_block.add_new_transaction(transaction)
                            new_block.close_block()
                            
                            if (new_block.header["hash"] == data_hash and
                                    new_block.header["hash"] == block_hash):
                                database.save_block(new_block)
                    return
                
                if data_request[1] == "close-block-response":
                    return
    
                if data_request[0] == 'leader-request':
                    print(f"Peer : {signing_peer.name} requesting for block_leader")
                    
                    self.send_message(signing_peer, str({"leader": self.chain_leader}),
                                      "leader-response", 1)
                    return
                
                if data_request[0] == 'leader-response':
                    # leader-response, {leader: True}
        
                    pos_chain_leader = data_request[1]
                    
                    if pos_chain_leader["leader"]:
                        self.chain_leader = signing_peer
                    return
                
                if data_request[0] == 'register-response':
                    # decrypt the recvd data
                    # decrypted data {respone : x}
                    decrypted_response = eval(identity.derypt_data(data_request[1]))
                    
                    print(f"Register response : {decrypted_response}")
                    if decrypted_response["response"] == "chains-equal":
                        print(f"Chain equal to {signing_peer.address}")
                        self.chains_to_validate[signing_peer.name] = 0
                        self.check_ready_to_download()
                        return
                    
                    elif decrypted_response["response"] == "-chain":
                        # my chain is smaller
                        print(f"my chainis smaller that : {signing_peer.name}")
                        self.chains_to_validate[signing_peer.name] = -1
                        self.check_ready_to_download()
                        return
                    
                    elif decrypted_response["response"] == "+chain":
                        self.chains_to_validate[signing_peer.name] = 1
                        self.check_ready_to_download()
                        return
                    
                    elif decrypted_response["response"] == "^hash":
                        # chain hashes are different but chains are equal
                        
                        self.chains_to_validate[signing_peer.name] = 2
                        self.check_ready_to_download()
                        return
            else:
                print('Invalid data')
        
        except ValueError as excpt:
            data_invalid = True
            print(f"Value Error : {excpt}")
        # reactor.callInThread(self.doStop())
        
    def request_block_leader(self):
        pass
    
    def check_ready_to_download(self):
        if self.peers.__len__() / self.chains_to_validate.__len__() >= 0.5:
            if -1 not in self.chains_to_validate.values():
                print("No peer greater than mine")
                self.chains_to_validate = {}
                return
            
            chian_validator = ChainValidator(self.peers, chain, database)
            if chian_validator.get_all_chains_tp():
                self.chains_to_validate = {}
                self.broadcast_message("chain-leader",
                                       "leader-request", 1)
        
        print(f"Peers less than 0.5")
                
        return
    
    def send_response(self, message, peer_address):
        # encrypt and send response
        self.transport.write(message, peer_address)
        return
    
    def broadcast_message(self, message, message_label, e):
        # send a signed and encrypted message to all peers
        for peer in self.peers:
            self.send_message(peer, message, message_label, e)
        return
    
    def send_message(self, peer:  Peer, message, message_label, e):
        message_to_send = [message_label, message]
        
        if e == 1:
            message_to_send = encrypt_data(rsa.PublicKey.load_pkcs1(peer.pk), message)
    
        unsinged_message = [message_label, message_to_send]
        signed_message = identity.sign_data(unsinged_message)
        self.transport.write(f"{signed_message}0000{unsinged_message}".encode('utf-8'),
                             peer.address)
        return


def add_transaction_to_block(transaction):
    global open_block
    added = open_block.add_new_transaction(transaction)
    if added is False:
        chain.add_new_block(open_block)
        database.save_block(open_block)
        open_block = Block()
        open_block.add_new_transaction(transaction)
    return
    

def grpc_server():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    block_pb2_grpc.add_BlockDownloaderServicer_to_server(BlockDownloader(chain), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


def block_time_monitor():
    # close block when not empty after a time limit and if you are the block leader
    # TODO block voting(concencus), allow for block leader, manipulate open_block_old
    start_time = time.time()
    
    while True:
        elapsed_time = time.time() - start_time
        return
        
    
def main():
    # all nodes must not use port 9009 -> its for node-list-server
    port = 5000
    reactor.listenUDP(port, Server('0.0.0.0', port))
    reactor.run()


# this only runs if the module was *not* imported
if __name__ == '__main__':
    try:
        JSONRPC_THREAD = threading.Thread(target=serve)
        JSONRPC_THREAD.start()
        
        GRPC_THREAD = threading.Thread(target=grpc_server)
        GRPC_THREAD.start()
        main()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as ex:
        print(F"Error :  {ex}")
