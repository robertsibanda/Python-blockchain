import sys
import threading
import time
import datetime
import socket
from concurrent import futures
from random import randint
from dataclasses import asdict, astuple

import grpc
import rsa
from jsonrpcserver import serve, method, Success
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

import block_pb2_grpc
from _grpc_client_helper import ChainValidator
from _grpc_server_helper import BlockDownloader
from _server_helper import process_peer_chain_request, new_node_regiser, \
    process_close_block, grpc_server, twisted_server

from blockchain.block import Block
from blockchain.blockchain import Chain
from blockchain.peer import Peer, peer_exists, save_peer
from blockchain.security import verify_data, encrypt_data
from blockchain.security.Identity import Identity
from blockchain.storage.database import Database
from blockchain.storage.onchain import load_all_blocks, save_transaction
from blockchain.trasanction import Transaction
from clients.rpc import create_account, view_records, update_permissions,  \
    get_block_data, insert_record, find_person, find_my_docs, Response

"""
*db_name* 
: the name of the database to connected
default is localhost : '127.0.0.1, 27017'

chain: the blockchain containing blocks and transactions

*load_all_blocks*
: loads all previously saved blocks
from the database onto the chain


*identity* 
: contains all the Node`s signing,
encrypting, decrypting and verifying functions

*transaction_queue*
: contains all the transactions received but
not yet written to the chain

*network_leader*
: closes the block

*next_network_leader*
: takes over after leader
or if leader goes down for a significant amt of time
"""

db_name = ''

try:
    db_name = sys.argv[1]
except IndexError:
    db_name = input("Enter database name : ")

if db_name == '':
    db_name = 'localhost'

database = Database(socket.gethostbyname(db_name), 27017, 'ehr_chain')

chain = Chain()

# load blocks saved before shutdown
load_all_blocks(database, chain)


# check if the chain from database is valid
if chain.is_valid() is not True:
    print("chain invalid XXXX")
    sys.exit()

# create an instance of the identity used to sign and encrypt data
identity = Identity()

# transaction queue of all transactions
transaction_queue = []

network_leader = None

next_network_leader = None

last_block_time = None
class Server(DatagramProtocol):
    def __init__(self, host, port):
        self.peers = set()
        self.id = '{}:{}'.format(host, port)
        self.address = (host, port)
        # self.server = socket.gethostbyname('node-reg'), 9009
        self.server = None

        try:
            self.server = socket.gethostbyname('node-reg'), 9009
        except:
            self.server = '172.19.0.2', 9009

        self.index_being_validated = 0
        self.new_join = True
        self.chain_leader = False
        self.chain_leader_n = None
        self.chains_to_validate = {}
        self.my_name = sys.argv[2]

        print('working on id : ', self.id)
    
    def startProtocol(self):
        """initialize the connection"""
        node_identity = {"status": "ready", 
            "pk": identity.public_key, "name": self.my_name}

        # send message to node_list_server to get peers
        self.transport.write(str(node_identity).encode('utf-8'), self.server)
    
    def datagramReceived(self, datagram: bytes, addr):
        
        global network_leader, next_network_leader, transaction_queue, last_block_time

        if addr[1] == self.server[1]:
            '''
            handle comms comming from node with register of
            online nodes
            '''
            data = datagram.decode().split('->')
        
            if data[1] == '':
                
                print("No peers in the network")

                network_leader = True
                last_block_time = datetime.datetime.today()

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

                    peer_recvd = eval(peer)
                    
                    new_node = Peer(peer_recvd["address"], 
                        peer_recvd["public_key"],peer_recvd["name"])

                    if peer_exists(self.peers, new_node):
                        continue
    
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
            print('Failed to decode data : ', excpt.__str__())

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
                
                print('Peer not found : brute force started ..........')
                
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
                
                if data_request[0] == "new block":
                    
                    print(f"data request : {data_request[1]}")

                    if signing_peer.name == network_leader:
                        
                        block_header = data_request[1][1]['header']
                        transactions = data_request[1][1]["transactions"]

                        pos_network_leader = data_request[1][1]['network_leader']

                        print(f"Block header 1: {block_header}")

                        data_hash = block_header["data_hash"]
                        block_hash = block_header["hash"]
                        block_prev_hash = block_header["prev_hash"]
                        
                        # respose { data_hash : '', block_hash : '' }
                        response = process_close_block(transaction_queue, list(transactions))
                        

                        if response["found"]:
                            new_block = Block()
                            for transaction in response["transactions"]:
                                new_block.add_new_transaction(transaction)
                            new_block.close_block()
                            
                            # add new block to chain
                            chain.add_new_block(new_block)
                            print(f"Block header 2: {new_block.header}")
                            print(f"Block 1 header : {block_header}")

                            if (new_block.header["data_hash"] == data_hash and
                                    new_block.header["hash"] == block_hash):
                                
                                last_block_time = datetime.datetime.today()

                                database.save_block(new_block)
                                print(f"Bloc saved to database {new_block.header}")
                            
                                if pos_network_leader == self.my_name:
                                    print(f"Network leader updated to me : {network_leader}")
                                    network_leader = True
                                    next_network_leader = list(self.peers)[randint(0, len(self.peers)-1)]
                                    next_network_leader = next_network_leader.name
                                else:
                                    print(f"I`m not network leader : {network_leader}")
                            else:
                                print("Block did not match")
                        else:
                            # some transactions not found
                            # request missing transactions
                            # and request latest savd block and save
                            pass
                    return
                
                if data_request[1] == "correct block":
                    # save the block 
                    return
    
                if data_request[0] == 'leader-request':
                    print(f"Peer : {signing_peer.name} requesting for block_leader")
                    
                    if not next_network_leader and len(self.peers) == 1:
                        next_network_leader = signing_peer.name
                        print(f"Changed next leader to : {signing_peer.name}")

                    self.send_message(signing_peer, str({"leader": network_leader, 
                        'next_leader' : next_network_leader}), "leader-response", 1)

                    return
                
                if data_request[0] == 'transaction':

                    transaction_data = data_request[1][1]

                    transaction = Transaction('','','','')
                    transaction._from_dict(transaction_data)

                    # works because its a 
                    save_transaction(database, transaction)
                    transaction_queue.append(transaction)
                    

                if data_request[0] == 'leader-response':
                    # leader-response, {leader: True}
        
                    pos_chain_leader = identity.derypt_data(data_request[1])
                    
                    chain_leader_data = eval(identity.derypt_data(data_request[1]))

                    if chain_leader_data["leader"] is True:

                        network_leader = signing_peer.name

                        next_network_leader = chain_leader_data['next_leader']

                        print(f"Leader node : {network_leader}")
                    
                    else:
                        print(f"{signing_peer.name} isn not a leader")
                    return
                
                if data_request[0] == 'register-response':
                    # decrypt the recvd data
                    # decrypted data {respone : x}
                    decrypted_response = eval(identity.derypt_data(data_request[1]))
                    
                    if decrypted_response["response"] == "chains-equal":
                        self.chains_to_validate[signing_peer.name] = 0
                        self.check_ready_to_download()
                        return
                    
                    elif decrypted_response["response"] == "-chain":
                        # my chain is smaller
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
                self.broadcast_message("chain-leader","leader-request", 1)
                self.chains_to_validate = {}
                return
            
            chian_validator = ChainValidator(self.peers, chain, database)
            chian_validator.get_all_chains_tp()
            self.chains_to_validate = {}
            self.broadcast_message("chain-leader","leader-request", 1)
            return

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
        return True
    
    def send_message(self, peer:  Peer, message, message_label, e):
        message_to_send = [message_label, message]
        
        if e == 1:
            message_to_send = encrypt_data(rsa.PublicKey.load_pkcs1(peer.pk), message)
    
        unsinged_message = [message_label, message_to_send]
        signed_message = identity.sign_data(unsinged_message)
        self.transport.write(f"{signed_message}0000{unsinged_message}"
            .encode('utf-8'),peer.address)
        return


port = 5000
server = Server('0.0.0.0', port)


"""
begining of other functions
"""

def broadcast_transction(transaction : Transaction) -> None:
    usnsigned_transaction_data = asdict(transaction)
    return server.broadcast_message(usnsigned_transaction_data, 'transaction', 0)


def create_block(transactions) -> Block:
    block = Block()
    [block.add_new_transaction(tx) for tx in transactions]
    block.close_block()
    chain.add_new_block(block)
    database.save_block(block)
    return block

def broadcast_new_block(new_block : Block):
    """
    notify other nodes about the new block
    """

    global next_network_leader

    block_data  = {
        'network_leader' : next_network_leader,
        'header' : new_block.header,
        'transactions' : [tx.hash for tx in new_block.transactions]
    }

    return server.broadcast_message(block_data, 'new block', 0)

def network_monitor():

    """
    monitor the network inorder
    to create new blocks timely
    """

    while True:

        global network_leader, next_network_leader, last_block_time

        if last_block_time == None:
            last_block_time = datetime.datetime.today()

        if network_leader is True:
            """
            only create new blocks when you are the network leader
            """

            if ((datetime.datetime.today() - last_block_time).seconds 
                 < 20) or (len(transaction_queue) < 10):
                """
                blocks created at 20 seconds intervals and
                when there are enough transactions to do so
                """
                # do not close the block
                reason ='time or transaction_queue size'
                print(reason)
            else:
                transactions = []

                # only 20 tx per block
                if len(transaction_queue) > 20:
                    transactions = transaction_queue[0:19]
                else:
                    transactions = transaction_queue.copy()

                for tx in transactions:
                    transaction_queue.remove(tx)

                new_block  = create_block(transactions)
                broadcast_new_block(new_block)

                network_leader = False
                network_leader= next_network_leader
        else:
            reason = 'wait for your chance'
            print(reason)

        time.sleep(1)

"""
begining of jsonrpc intermediary methods
"""


@method
def signup(headers):
    print("Request recieved : ", headers)

    result = create_account(database, headers)

    if isinstance(result, Transaction):
        transaction_queue.append(result)
        if broadcast_transction(result):
            return Success({ "success" : result.data['userid']})
    else:
        return Success(result)
    print(transaction_queue)


@method
def update_records(headers):
    result = insert_record(database, headers)

    if isinstance(result, Transaction):
        transaction_queue.append(result)
        broadcast_transction(result)
    else:
        return Success(result)

    return Success({ "success" : "record added" })


@method
def view_health_records(headers):
    response = view_records(database, headers)
    # print("Transction created : " , transaction.hash, ' -> ', transaction.data )
    if isinstance(response, Response):
        transaction = response.transaction
        transaction_queue.append(transaction)
        broadcast_transction(transaction)
        return Success({ "success" : response.response})
    else: 
        return Success(response)


@method
def update_data_permissions(headers):
    result = update_permissions(database, headers)

    if isinstance(result, Transaction):
        transaction_queue.append(result)
        broadcast_transction(result)
    else:
        return Success(result)
        
    return Success({ "success" : "permission added" })

@method 
def get_my_doctors(headers):
    result = find_my_docs(database, headers)
    if len(result) == 0:
        return Success({ 'success' : 'no users found'})
    else:
        return Success({ 'success' : result})

@method
def search_person(headers):
    result = find_person(database, headers)

    if len(result) == 0:
        return Success({ 'error' : 'no user found'})
        
    else: return Success({ 'success' : result})

@method
def delete_account(headers):
    return

"""
end of rpc intermediary methods
"""



# this only runs if the module was *not* imported
if __name__ == '__main__':
    try:
        jsonrpc_thread = threading.Thread(target=serve)
        jsonrpc_thread.start()
        
        grpc_thread = threading.Thread(target=grpc_server, args=[chain])
        grpc_thread.start()

        network_monitor_thread = threading.Thread(target=network_monitor)
        network_monitor_thread.start()

        twisted_server(server)

    except KeyboardInterrupt:
        sys.exit()
    except Exception as ex:
        print(F"Error :  {ex}")
