import base64
import json
import sys
import threading
import time
import datetime
import socket
from random import randint
from dataclasses import asdict

import rsa
from jsonrpcserver import serve, method
from twisted.internet.protocol import DatagramProtocol

from _grpc_client_helper import ChainValidator
from _server_helper import new_node_register, \
    process_close_block, grpc_server, twisted_server

from blockchain.block import Block
from blockchain.blockchain import Chain
from blockchain.peer import Peer, peer_exists
from blockchain.security import verify_data, encrypt_data
from blockchain.security.Identity import Identity
from blockchain.storage.database import Database
from blockchain.storage.onchain import load_all_blocks, save_transaction
from blockchain.transaction import Transaction

"""
Variables:
    db_name: The name of the MongoDB database to connect to (default: localhost).
    chain: The blockchain containing blocks and transactions.
    load_all_blocks: Loads all previously saved blocks from the database onto the chain.
    identity: Contains all the node's signing, encrypting, decrypting, and verifying functions.
    transaction_queue: Contains all transactions received but not yet written to the chain.
    network_leader: The node responsible for closing the current block.
    next_network_leader: Takes over after the leader or if the leader goes down.
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
    """Main blockchain node server handling peer-to-peer communication via UDP."""

    def __init__(self, host, port):
        self.peers = set()
        self.id = '{}:{}'.format(host, port)
        self.address = (host, port)
        self.server = None

        try:
            self.server = socket.gethostbyname('node-reg'), 9009
        except Exception:
            self.server = '172.20.0.1', 9009

        self.index_being_validated = 0
        self.new_join = True
        self.chain_leader = False
        self.chain_leader_n = None
        self.chains_to_validate = {}
        self.my_name = sys.argv[2]

        print('working on id : ', self.id)

    def startProtocol(self):
        """Send registration message to the node list server on startup."""
        pk_pem = identity.public_key.save_pkcs1("PEM").decode('utf-8')
        node_identity = {"status": "ready",
                         "pk": pk_pem, "name": self.my_name}
        self.transport.write(json.dumps(node_identity).encode('utf-8'), self.server)

    def datagramReceived(self, datagram: bytes, addr):
        """Handle incoming UDP datagrams from the node list server and peer nodes."""
        global network_leader, next_network_leader, transaction_queue, last_block_time

        if addr[1] == self.server[1]:
            self._handle_node_list_server(datagram, addr)
            return

        try:
            recvd_data = datagram.decode().split('0000')
        except Exception as excpt:
            print('Failed to decode data : ', excpt.__str__())
            return

        try:
            signing_peer = None
            verified_data = False

            for peer in self.peers:
                if peer.address == addr:
                    signing_peer = peer

            if signing_peer is None:
                print('Peer not found : brute force started ..........')
                for peer in self.peers:
                    try:
                        verified_data = verify_data(
                            recvd_data[1].encode('utf-8'),
                            base64.b64decode(recvd_data[0]),
                            rsa.PublicKey.load_pkcs1(peer.pk))
                    except rsa.VerificationError:
                        continue
                    if verified_data:
                        print(f"Peer found updating from {peer.address} to {addr}")
                        peer.address = addr
                        break
                if signing_peer is None:
                    return
            else:
                verified_data = verify_data(
                    recvd_data[1].encode('utf-8'),
                    base64.b64decode(recvd_data[0]),
                    rsa.PublicKey.load_pkcs1(signing_peer.pk))

            if verified_data:
                self._handle_peer_message(recvd_data, signing_peer)
            else:
                print('Invalid data')

        except ValueError as excpt:
            print(f"Value Error : {excpt}")

    def _handle_node_list_server(self, datagram: bytes, addr: tuple) -> None:
        """Process messages received from the central node list server."""
        global network_leader, last_block_time

        data = datagram.decode().split('->')

        if data[1] == '':
            print("No peers in the network")
            network_leader = True
            last_block_time = datetime.datetime.today()
            print(f"I am network leader : {network_leader}")
            self.new_join = False
            return

        if data[0] == 'peers':
            recvd_peers = data[1].split('::::')
            for p in recvd_peers:
                print(f"Peer {p}")

            new_node = None
            for peer in recvd_peers:
                if not peer.strip():
                    continue
                peer_recvd = json.loads(peer)
                new_node = Peer(peer_recvd["address"],
                                peer_recvd["public_key"], peer_recvd["name"])
                if peer_exists(self.peers, new_node):
                    continue
                self.peers.add(new_node)

            if self.new_join:
                self.chains_to_validate[new_node.name] = 0
                message = {"chain-length": f"{len(chain.chain)}",
                           "last-block": chain.get_last_block().header["hash"]}
                self.broadcast_message(message, 'register', 0)
                self.new_join = False

            print('\nPeers :{}'.format(
                [f'\t{peer.name}' for peer in self.peers]))

    def _handle_peer_message(self, recvd_data: list, signing_peer: Peer) -> None:
        """Process verified messages received from peer nodes."""
        global network_leader, next_network_leader, transaction_queue, last_block_time

        data_request = json.loads(recvd_data[1])

        if data_request[0] == 'register':
            new_node_chain_props = data_request[1]
            response = new_node_register(
                new_node_chain_props, chain, self.transport, signing_peer)
            self.send_message(signing_peer, response, "register-response", 1)

        elif data_request[0] == "new block":
            if signing_peer.name == network_leader:
                block_header = data_request[1][1]['header']
                transactions = data_request[1][1]["transactions"]
                pos_network_leader = data_request[1][1]['network_leader']
                data_hash = block_header["data_hash"]
                block_hash = block_header["hash"]

                response = process_close_block(
                    transaction_queue, list(transactions))

                if response["found"]:
                    new_block = Block()
                    for transaction in response["transactions"]:
                        new_block.add_new_transaction(transaction)
                    new_block.close_block()
                    chain.add_new_block(new_block)

                    if (new_block.header["data_hash"] == data_hash and
                            new_block.header["hash"] == block_hash):
                        last_block_time = datetime.datetime.today()
                        database.save_block(new_block)
                        print(f"Block saved to database {new_block.header}")

                        if pos_network_leader == self.my_name:
                            network_leader = True
                            next_network_leader = list(self.peers)[
                                randint(0, len(self.peers) - 1)]
                            next_network_leader = next_network_leader.name
                    else:
                        print("Block did not match")

        elif data_request[0] == 'leader-request':
            print(f"Peer : {signing_peer.name} requesting for block_leader")
            if not next_network_leader and len(self.peers) == 1:
                next_network_leader = signing_peer.name
            self.send_message(signing_peer, str({"leader": network_leader,
                                                  'next_leader': next_network_leader}),
                              "leader-response", 1)

        elif data_request[0] == 'transaction':
            transaction_data = data_request[1][1]
            transaction = Transaction('', '', '', '')
            transaction._from_dict(transaction_data)
            save_transaction(database, transaction)
            transaction_queue.append(transaction)

        elif data_request[0] == 'leader-response':
            encrypted_payload = base64.b64decode(data_request[1][1])
            decrypted_str = identity.decrypt_data(encrypted_payload)
            chain_leader_data = json.loads(decrypted_str)
            if chain_leader_data["leader"] is True:
                network_leader = signing_peer.name
                next_network_leader = chain_leader_data['next_leader']
                print(f"Leader node : {network_leader}")
            else:
                print(f"{signing_peer.name} is not a leader")

        elif data_request[0] == 'register-response':
            encrypted_payload = base64.b64decode(data_request[1][1])
            decrypted_str = identity.decrypt_data(encrypted_payload)
            decrypted_response = json.loads(decrypted_str)
            response_map = {
                "chains-equal": 0,
                "-chain": -1,
                "+chain": 1,
                "^hash": 2,
            }
            status = response_map.get(decrypted_response["response"])
            if status is not None:
                self.chains_to_validate[signing_peer.name] = status
                self.check_ready_to_download()

    def request_block_leader(self) -> None:
        """Placeholder: request to become the block leader."""
        pass

    def check_ready_to_download(self) -> None:
        """Check if enough peers have responded and initiate chain download if needed."""
        if len(self.peers) / max(len(self.chains_to_validate), 1) >= 0.5:
            if -1 not in self.chains_to_validate.values():
                print("No peer greater than mine")
                self.broadcast_message("chain-leader", "leader-request", 1)
                self.chains_to_validate = {}
                return
            chain_validator = ChainValidator(self.peers, chain, database)
            chain_validator.get_all_chains_tp()
            self.chains_to_validate = {}
            self.broadcast_message("chain-leader", "leader-request", 1)
            return
        print("Peers less than 0.5")

    def send_response(self, message: bytes, peer_address: tuple) -> None:
        """Send a raw response to a peer address."""
        self.transport.write(message, peer_address)

    def broadcast_message(self, message, message_label: str, e: int) -> bool:
        """Send a signed message to all connected peers.

        Args:
            message: The message content.
            message_label: The message type label.
            e: Encryption flag (1 = encrypt payload).
        """
        for peer in self.peers:
            self.send_message(peer, message, message_label, e)
        return True

    def send_message(self, peer: Peer, message, message_label: str, e: int) -> None:
        """Send a signed (and optionally encrypted) message to a specific peer.

        Args:
            peer: The target peer.
            message: The message payload.
            message_label: The message type label.
            e: Encryption flag (1 = encrypt with peer's public key).
        """
        import base64

        message_to_send = [message_label, message]

        if e == 1:
            encrypted = encrypt_data(
                rsa.PublicKey.load_pkcs1(peer.pk), message)
            message_to_send = [message_label, base64.b64encode(encrypted).decode('utf-8')]

        unsigned_message = [message_label, message_to_send]
        signed_message = identity.sign_data(unsigned_message)
        sig_b64 = base64.b64encode(signed_message).decode('utf-8')
        data_json = json.dumps(unsigned_message)
        self.transport.write(
            f"{sig_b64}0000{data_json}".encode('utf-8'), peer.address)


port = 5000
server = Server('0.0.0.0', port)


"""
beginning of other functions
"""


def broadcast_transaction(transaction: Transaction) -> None:
    usnsigned_transaction_data = asdict(transaction)
    return server.broadcast_message(usnsigned_transaction_data, 'transaction', 0)


def create_block(transactions) -> Block:
    block = Block()
    [block.add_new_transaction(tx) for tx in transactions]
    block.close_block()
    chain.add_new_block(block)
    database.save_block(block)
    return block


def broadcast_new_block(new_block: Block):
    """Notify other nodes about the new block."""

    global next_network_leader

    block_data = {
        'network_leader': next_network_leader,
        'header': new_block.header,
        'transactions': [tx.hash for tx in new_block.transactions]
    }

    return server.broadcast_message(block_data, 'new block', 0)


def network_monitor():
    """Monitor the network and create new blocks when conditions are met."""

    while True:

        global network_leader, next_network_leader, last_block_time
        MAX_TIME = 100
        MAX_TRANSACTIONS = 5

        print(f"\nNetwork leader {network_leader}")

        if last_block_time == None:
            last_block_time = datetime.datetime.today()

        if network_leader is True:
            """
            only create new blocks when you are the network leader
            """

            if ((datetime.datetime.today() - last_block_time).seconds
                    < MAX_TIME) and (len(transaction_queue) < MAX_TRANSACTIONS):
                """
                blocks created at MAX_TIME seconds intervals and
                when there are enough transactions MAX_TRANSACTIONS to do so
                """
                # do not close the block
                reason = 'time or transaction_queue size'
                print(f"Transaction queue : {transaction_queue} - > {reason}")
                # print(reason)
            else:
                if len(transaction_queue) > 1:
                    transactions = []

                    # only MAX_TRANSACTIONS per block
                    if len(transaction_queue) > MAX_TRANSACTIONS:
                        transactions = transaction_queue[0:MAX_TRANSACTIONS]
                    else:
                        transactions = transaction_queue.copy()

                    for tx in transactions:
                        transaction_queue.remove(tx)

                    new_block = create_block(transactions)
                    broadcast_new_block(new_block)

                    network_leader = False
                    network_leader = next_network_leader

                    if network_leader == None:
                        network_leader = True
        else:
            reason = 'wait for your chance'
            print(f"Transaction queue : {transaction_queue} - > {reason}")
            # print(reason)

        time.sleep(0.5)


"""
beginning of jsonrpc intermediary methods
"""

@method
def transact(headers):
    return



"""
end of rpc intermediary methods
"""


# this only runs if the module was *not* imported
if __name__ == '__main__':
    try:
        # rpc server for Node to client comms
        jsonrpc_thread = threading.Thread(target=serve)
        jsonrpc_thread.start()

        # grpc for Node to Node comms
        grpc_thread = threading.Thread(target=grpc_server, args=[chain])
        grpc_thread.start()

        network_monitor_thread = threading.Thread(target=network_monitor)
        network_monitor_thread.start()

        # twisted for Node to Node comms of smaller messages
        twisted_server(server)

    except KeyboardInterrupt:
        sys.exit()
    except Exception as ex:
        print(F"Error :  {ex}")
