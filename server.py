# Robert Sibanda (robertsibanda20@gmail.com)
# .
# this is the Node server file
import time
import sys
import threading
import rsa
from random import randint, random
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from jsonrpcserver import serve, method, Success
from BlockChain.Trasanction import Transaction
from BlockChain.BlockChain import Chain
from BlockChain.Block import Block
from BlockChain.Peer import Peer, peer_exists, save_peer
from BlockChain.Security.Identity import Identity
from BlockChain.Security import verify_data, encrypt_data
from BlockChain.Storage.Database import Database
from Clients.rpc import get_block, is_chain_valid, register_new_practitioner

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

chains_to_validate = {}

# open block for adding new transactions
open_block = Block()


class Server(DatagramProtocol):
    
    def __init__(self, host, port):
        self.peers = set()
        self.id = '{}:{}'.format(host, port)
        self.address = (host, port)
        self.server = '0.0.0.0', 9009
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
                                             {
                                                "chain-length": f"{len(chain.chain)}",
                                                "last-block": chain.get_last_block().header["hash"]
                                                
                                                }
                                             ]
                        
                        signed_data = identity.sign_data(data_to_broadcast)
                        self.transport.write(
                            f"{signed_data}0000{data_to_broadcast}".encode("utf-8"),
                            new_node.address)
                
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
            
            for peer in self.peers:
                if peer.address == addr:
                    signing_peer = peer
            
            print('Signing peer : ', signing_peer.address)
            print('recieved data : ', recvd_data)
            
            verified_data = verify_data(recvd_data[1].encode('utf-8'),
                                        eval(recvd_data[0]),
                                        rsa.PublicKey.load_pkcs1(signing_peer.pk)
                                        )
            
            if verified_data:
                
                print(f"Data recvd from peer {eval(recvd_data[1])}")
                
                data_request = eval(recvd_data[1])  # recvd_data is list [str, dict]
                print(f"type of recvd data  : {type(data_request)}")
                
                if data_request[0] == 'register':
                    """
                    new node requesting chain
                    send chain hashes only
                    """
                    
                    # dict with properties of the request
                    # {chain-length : x, last-block : y}
                    
                    print(f"new node props : {data_request[1]}")
                    print(f"type new node props : {type(data_request[1])}")
                    
                    new_node_chain_props = data_request[1]
                    
                    # properties of my chain
                    my_chain_props = {
                        "chain-length": str(len(chain.chain)),
                        "last-block": chain.get_last_block().header["hash"]
                        }
                    
                    if new_node_chain_props == my_chain_props:
                        # chains are at the same level and are probably equal
                        # send response notifying new node that chains at same level
                        
                        register_response = {
                            "response": "chains-equal"
                            }
                        
                        encrypted_response = [
                            "register-response",
                                encrypt_data(rsa.PublicKey.load_pkcs1(signing_peer.pk),register_response),
                            ]
                        
                        signed_encrypted_response = identity.sign_data(encrypted_response)
                        
                        self.transport.write(f"{signed_encrypted_response}0000"
                                             f"{encrypted_response}"
                                             .encode('utf-8'),
                                             signing_peer.address)
                        return
                    
                    if new_node_chain_props != my_chain_props:
                        
                        # check length of chain
                        if (my_chain_props["chain-length"] >
                                new_node_chain_props["chain-length"]):
                            
                            # my chain is higher that new node chain
                            # send response notifying of my chain size and other blocks
                            return
                        
                        elif (my_chain_props["chain-length"] <
                              new_node_chain_props["chain-length"]):
                            
                            # my chain is smaller than new node chain
                            # request other missing blocks
                            return
                        
                        elif (my_chain_props["chain-length"] ==
                              new_node_chain_props["chain-length"]):
                            
                            # chain size is the same with unmatching block hashes
                            # one / all the chains are incorrect
                            # check validity of chains
                            return
                    return
                
                if data_request[0] == 'register-response':
                    
                    # decrypt the recvd data
                    # decrypted data {respone : x}
                    decrypted_response = eval(identity.derypt_data(data_request[1]))
                    
                    if decrypted_response["response"] == "chains-equal":
                        print(f"Chain equal to {signing_peer.address}")
                        return
                    
                    elif decrypted_response["response"] == "-chain":
                        # my chain is smaller
                        return
                    
                    elif decrypted_response["response"] == "+chain":
                        # my chain is larger
                        return
                    
                    elif decrypted_response["response"] == "+chain+":
                        # chains are different
                        return
                    
                
                if recvd_data[1].startswith('chain-index-'):
                    """
                    send the requested hashed to peer
                    """
                    self.respondbroadcast_chain_request(recvd_data[1], addr)
                    return
                
                if recvd_data[2].endswith('hashes-requested'):
                    """
                    process the recvd hashed from peer
                    """
                    self.process_recvd_hashes(recvd_data[2], addr)
                
                if recvd_data[2] == 'chain-hashes':
                    chains_to_validate[addr] = recvd_data[1]
                    
                    """
                    check of the majority of the peers have sent their hashlist
                    """
                    if len(chains_to_validate.values()) / len(self.peers) >= 0.51:
                        """
                        start chain requests to peers
                        """
                        self.broadcast_chain_request()
                    
                    else:
                        """
                        create a timestamp for the last chain recieved
                        check after 10 minutes if the remaining peers are still alive
                        if alive -> send another hash request
                        if dead  -> remove from self.peers and recalculate
                                    the number of peers required
                        """
                        return
                
                if eval(recvd_data)[1] == "chain":
                    """
                    validate the chain and copy
                    """
                    return
                
                if eval(recvd_data)["type"] == "transaction":
                    """
                    verify and add new transaction block
                    """
                    return
                
                for blk in chain.chain:
                    print('\nBlock ', chain.chain.index(blk))
                    print(blk)
            else:
                print('Invalid data')
        
        except rsa.VerificationError:
            data_invalid = True
            print("Verification Error : data may have been altered in transit")
        
        reactor.callInThread(self.send_message)
    
    def broadcast_chain_request(self):
        for peer_addr in chains_to_validate.values():
            data2send = 'chain-index-{}'.format(self.index_being_validated)
            signed_data = identity.sign_data(data2send)
            signed_data2send = '{}0000{}'.format(signed_data, data2send)
            self.transport.write(signed_data2send.encode('utf-8'), peer_addr)
        
        return
    
    def respondbroadcast_chain_request(self, data, addr):
        chain_index = data[1].split()[-1]
        block_hashes2send = (
            chain.chain[chain_index].hash, chain.chain[chain_index].prev_hash)
        signed_blockhashes = identity.sign_data(block_hashes2send)
        self.transport.write(
            '{}0000{}0000chain-index-{}-hashes-requested'.format(signed_blockhashes,
                                                                 block_hashes2send,
                                                                 chain_index
                                                                 ), addr
            )
        return
    
    def process_recvd_hashes(self, data, addr):
        if self.index_being_validated == 0:
            """
            ignore link check if block is genesis
            perfom data check
            block data -> (hash, prev_hash)
            """
            block_data = eval(data)
        
        else:
            """
            perfom link check and data check
            """
            pass
        
        self.index_being_validated += 1
        
        self.broadcast_chain_request()
    
    def send_message(self):
        while True:
            data = input('::::')
            '''
            sign data before sending
            send message and signature
            '''
            singed_data = identity.sign_data(data)
            chain.add_new_block(Block('0', data))
            try:
                for peer in self.peers:
                    self.transport.write(
                        '{}0000{}'.format(singed_data, data).encode('utf-8'), peer
                        )
                for blk in chain.chain:
                    print(
                        '\n\nBlock ######\nprev hash : {}\ndata : {}\n hash : {}'.format(
                            blk.prev_hash, blk.data, blk.hash
                            )
                        )
            except RuntimeError:
                ignore_error = True
    
    def validate_peer_chain(self, peer: Peer):
        """
        Validate a Peers` chain based on others` chains
        """
        self.transport.write()
        
        pass


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


def main():
    # all nodes must not use port 9009 -> its for node-list-server
    port = randint(1000, 5000)
    reactor.listenUDP(port, Server('0.0.0.0', port))
    reactor.run()


# this only runs if the module was *not* imported
if __name__ == '__main__':
    try:
        RPC_THREAD = threading.Thread(target=serve)
        # RPC_THREAD.start()
        main()
    except KeyboardInterrupt:
        sys.exit()
