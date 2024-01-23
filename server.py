# Robert Sibanda (robertsibanda20@gmail.com)
# .
# this is the Node server file
import sys
import threading
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
from _server_helper import process_peer_chain_request
from blockchain.block import Block
from blockchain.blockchain import Chain
from blockchain.peer import Peer, peer_exists, save_peer
from blockchain.security import verify_data, encrypt_data
from blockchain.security.Identity import Identity
from blockchain.storage.database import Database
from blockchain.trasanction import Transaction
from clients.rpc import register_new_practitioner



database = Database('127.0.0.1', 27017, 'ehr_chain')

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

chains_to_validate = []

# open block for adding new transactions
open_block = Block()


class Server(DatagramProtocol):
    
    def __init__(self, host, port):
        self.peers = set()
        self.id = '{}:{}'.format(host, port)
        self.address = (host, port)
        self.server = '192.168.43.252', 9009
        self.index_being_validated = 0
        self.new_join = True
        print('working on id : ', self.id)
    
    def startProtocol(self):
        """initialize the connection"""
        node_identity = {"status": "ready", "pk": identity.public_key, "name": "node-1"
                         }
        self.transport.write(str(node_identity).encode('utf-8'), self.server)
    
    def datagramReceived(self, datagram: bytes, addr):
        """
        process data received from others peers
        register    - peer registering itself on the network
        peers       - list of all peers that are currently
                       live on the network
        transaction - a data transaction
        status      - chech the status of nodes on the network
        """
        if addr[1] == self.server[1]:
            '''
            handle comms comming from node with register of
            online nodes
            '''
            data = datagram.decode().split('->')
            
            if data[0] == 'peers':
                print(f"Data recieved from node-list-srver {data}")
                """
                if node was already running update list of peers
                """
                
                if data[1] == '':
                    print("No peers in the network")
                    self.new_join = False
                    return
                
                recvd_peers = data[1].split('::::')
                
                for peer in recvd_peers:
                    print('Peer address : ', eval(peer)["address"])
                    if peer_exists(self.peers, peer):
                        continue
                    
                    peer_recvd = eval(peer)
                    
                    save_peer(database, peer_recvd)
                    new_node = Peer(peer_recvd["address"], peer_recvd["public_key"],
                                    peer_recvd["name"]
                                    )
                    
                    """
                    add new node to list of currently registered nodes
                    """
                    
                    self.peers.add(new_node)
                    
                    if self.new_join:
                        """
                        only register and request chain if new node
                        """
                        data_to_broadcast = ["register",
                                             {"chain-length": f"{len(chain.chain)}",
                                              "last-block": chain.get_last_block().header[
                                                  "hash"]
                                                  
                                              }]
                        
                        signed_data = identity.sign_data(data_to_broadcast)
                        self.transport.write(
                            f"{signed_data}0000{data_to_broadcast}".encode("utf-8"),
                            new_node.address
                            )
                
                self.new_join = False
                print('\nPeers :\n{}'.format(self.peers))
            return
        
        """
        handle comms comming from other peer nodes
        """
        recvd_data = ''
        
        try:
            recvd_data = datagram.decode().split('0000')
        except Exception as ex:
            print('Failed to decode data : ', ex.__notes__)
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
                        verified_data = verify_data(recvd_data[1].encode('utf-8'),
                                                    eval(recvd_data[0]),
                                                    rsa.PublicKey.load_pkcs1(peer.pk)
                                                    )
                    except rsa.VerificationError:
                        continue
                    
                    if verified_data:
                        # update the peer address
                        print(f"Peer found updating from {peer.address} to {addr}")
                        peer.address = addr
                        break
                
                if signing_peer is None:
                    # peer not found throught brutefore
                    # inform node_list_server
                    return
            
            else:
                print('Signing peer : ', signing_peer.address)
                print('recieved data : ', recvd_data)
                
                verified_data = verify_data(recvd_data[1].encode('utf-8'),
                                            eval(recvd_data[0]),
                                            rsa.PublicKey.load_pkcs1(signing_peer.pk)
                                            )
            
            if verified_data:
                print(f"Data recvd from peer {eval(recvd_data[1])}")
                
                data_request = eval(recvd_data[1])  # recvd_data is list [str, dict]
                # print(f"type of recvd data  : {type(data_request)}")
                
                if data_request[0] == 'register':
                    """
                    new node requesting chain
                    send chain hashes only
                    """
                    
                    # dict with properties of the request
                    # {chain-length : x, last-block : y}
                    
                    new_node_chain_props = data_request[1]
                    
                    # properties of my chain
                    my_chain_props = {"chain-length": str(len(chain.chain)),
                                      "last-block": chain.get_last_block().header["hash"]
                                      }
                    
                    if new_node_chain_props == my_chain_props:
                        # chains are at the same level and are probably equal
                        # send response notifying new node that chains at same level
                        
                        register_response = {"response": "chains-equal"}
                        
                        encrypted_response = ["register-response", encrypt_data(
                            rsa.PublicKey.load_pkcs1(signing_peer.pk), register_response
                            )]
                        
                        signed_encrypted_response = identity.sign_data(encrypted_response)
                        
                        return f"{signed_encrypted_response}0000{encrypted_response}".encode(
                            'utf-8'
                            )
                    
                    if new_node_chain_props != my_chain_props:
                        # check length of chain
                        if (my_chain_props["chain-length"] >
                                new_node_chain_props["chain-length"]):
                            # my chain is higher that new node chain
                            # send response notifying of my chain size and other blocks
                            register_response = {"response": "-chain"}
                            encrypted_response = ["register-response", encrypt_data(
                                rsa.PublicKey.load_pkcs1(signing_peer.pk),
                                register_response
                                )]
                            signed_encrypted_response = identity.sign_data(
                                encrypted_response
                                )
                            self.transport.write(f"{signed_encrypted_response}0000{encrypted_response}"
                                    .encode('utf-8'), signing_peer.address)
                        
                        elif (my_chain_props["chain-length"] <
                              new_node_chain_props["chain-length"]):
                            # my chain is smaller than new node chain
                            # request other missing blocks
                            register_response = {"response": "+chain"}
                            encrypted_response = ["register-response", encrypt_data(
                                rsa.PublicKey.load_pkcs1(signing_peer.pk),
                                register_response
                                )]
                            signed_encrypted_response = (
                                identity.sign_data(encrypted_response))
                            
                            self.transport.write(f"{signed_encrypted_response}0000"
                                                 f"{encrypted_response}".encode('utf-8'),
                                                 signing_peer.address)
                            
                            # TODO initiate chain downloading protocol
                            
                        elif (my_chain_props["chain-length"] ==
                              new_node_chain_props["chain-length"]):
                            
                            # chain size is the same with unmatching block hashes
                            # one / all the chains are incorrect
                            # check validity of chains
                            register_response = {"response": "^hash"}
                            encrypted_response = ["register-response", encrypt_data(
                                rsa.PublicKey.load_pkcs1(signing_peer.pk),
                                register_response
                                )]
                            signed_encrypted_response = identity.sign_data(
                                encrypted_response
                                )
                            self.transport.write(f"{signed_encrypted_response}0000{encrypted_response}".encode(
                                'utf-8'), signing_peer.address)
                        
                if data_request[0] == 'register-response':
                    # decrypt the recvd data
                    # decrypted data {respone : x}
                    decrypted_response = eval(identity.derypt_data(data_request[1]))
                    
                    if decrypted_response["response"] == "chains-equal":
                        print(f"Chain equal to {signing_peer.address}")
                        return
                    
                    elif decrypted_response["response"] == "-chain":
                        # my chain is smaller
                        chain_hashes_request = {"response": "get-chain-hashed"}
                        encrypted_response = [
                            "get-chain-hashes",
                            encrypt_data(rsa.PublicKey.load_pkcs1(
                            signing_peer.pk), chain_hashes_request)]
                        
                        signed_encrypted_response = identity.sign_data(encrypted_response)
                        self.transport.write(f"{signed_encrypted_response}0000{encrypted_response}".
                                             encode('utf-8'), signing_peer.address)
                    
                    elif decrypted_response["response"] == "+chain":
                        # my chain is larger
                        return
                    
                    elif decrypted_response["response"] == "^hash":
                        # chain hashes are different but chains are equal
                        return
                
                if data_request[0] == 'get-chain-hashes':
                    # get the block hashes from the chain
                    print(f"{signing_peer.address} requesting chian hashs")
                    response = process_peer_chain_request(chain)
                    
                    # creeate a response
                    chain_hashes_response = {"chain": response}
                    encrypted_response = ["chain-hashes", encrypt_data(rsa.PublicKey.load_pkcs1(
                            signing_peer.pk), chain_hashes_response)]
                    signed_encrypted_response = identity.sign_data(encrypted_response)
                    self.transport.write(f"{signed_encrypted_response}0000{encrypted_response}"
                                         .encode('utf-8'), signing_peer.address)
                    
                if data_request[0] == 'chain-hashes':
                    # process chain hashes recieved from peer
                    # must consider hashes from multiple peers
                    chain_hash_data = identity.derypt_data(data_request[1])
                    print(f"Hashes recieved from {signing_peer.name}")
                    print(chain_hash_data)
                    
                    # add hashes to chains to validate
                    # handle chain copying and validation in separate thread
                    chains_to_validate.append({
                        signing_peer.name: eval(chain_hash_data)["chain"]
                        })
                    
                    # download_peer_blocks(signing_peer.address[0], chain,
                    # str(chain.get_last_block().header["hash"]), database)
                    
                    chian_validator = ChainValidator(self.peers, chain.get_last_block(),
                                                     chain, database)
                    chian_validator.get_all_chains()
                    return
                
                for blk in chain.chain:
                    print('\nBlock ', chain.chain.index(blk))
                    print(blk)
            else:
                print('Invalid data')
        
        except Exception as ex:
            data_invalid = True
            print(f"Error : {ex}")
        
        # reactor.callInThread(self.doStop())
    
    def send_response(self, message, peer_address):
        # encrypt and send response
        self.transport.write(message, peer_address)
        return
    
    def broadcast_message(self, message, message_label):
        # send a signed and encrypted message to all peers
        for peer in self.peers:
            self.send_message(peer, message, message_label)
        return
    
    def send_message(self, peer, message, message_label):
        encypted_message = encrypt_data(peer.pk, message)
        unsinged_message = {message_label: encypted_message}
        signed_message = identity.sign_data(unsinged_message)
        self.transport.write(f"{signed_message}0000{unsinged_message}")
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


@method
def reg_new_practitioner(details):
    result = register_new_practitioner(database, details)
    if result == 'acc_created':
        tr = Transaction('account verification', details, metadata=None)
        add_transaction_to_block(tr)
        return Success({"Message": "account created successfully"})
    return result


def rpc_server():
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    block_pb2_grpc.add_BlockDownloaderServicer_to_server(BlockDownloader(chain), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


def main():
    # all nodes must not use port 9009 -> its for node-list-server
    port = randint(1000, 5000)
    reactor.listenUDP(port, Server('192.168.43.252', port))
    reactor.run()


# this only runs if the module was *not* imported
if __name__ == '__main__':
    try:
        JSONRPC_THREAD = threading.Thread(target=serve)
        JSONRPC_THREAD.start()
        
        GRPC_THREAD = threading.Thread(target=rpc_server)
        GRPC_THREAD.start()
        main()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as ex:
        print(F"Error :  {ex}")
