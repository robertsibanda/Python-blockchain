# Robert Sibanda (robertsibanda20@gmail.com)
# .

# this is the Node server file

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from BlockChain.BlockChain import Chain
from BlockChain.Block import Block
from random import randint, random
from BlockChain.Peer import Peer, peer_exists, save_peer
from BlockChain.Security.Identity import Identity, verify_data, encrypt_data
from BlockChain.Storage.Database import Database
import rsa

database = Database('127.0.0.1', 27017, 'ehr_chain')

chain = Chain([])

identity = Identity()

other_nodes = {
}

chains_to_validate = {}


class Server(DatagramProtocol):

    def __init__(self, host, port):
        self.peers = set()
        self.id = '{}:{}'.format(host, port)
        self.address = (host, port)
        self.server = '192.168.56.1', 9009
        self.index_being_validated = 0
        self.new_join = True
        print('working on id : ', self.id)

    def startProtocol(self):
        """initialize the connection"""
        node_identity = {"status": "ready",
                         "pk": identity.public_key, "name": "node-{}".format(str(random())[2:])}
        self.transport.write(str(node_identity).encode('utf-8'), self.server)

    def datagramReceived(self, datagram: bytes, addr):
        """"
        process data received from others peers

        register    - peer registering itself on the network
        peers       - list of all peers that are currently
                       live on the network
        transaction - a data transaction
        status      - chech the status of nodes on the network
        """

        if addr == self.server:
            '''
            handle comms comming from node with register of
            online nodes
            '''
            data = datagram.decode().split('->')
            if data[0] == 'peers':

                """
                if node was already running update list of peers
                """
                if data[1] == '':
                    return

                recvd_peers = data[1].split('000000')

                if len(recvd_peers) < 2:
                    """no other peers in the network"""
                    return

                for peer in recvd_peers:

                    if peer_exists(self.peers, eval(peer)["address"]):
                        continue

                    if eval(peer)["address"] == self.address:
                        continue

                    peer_recvd = eval(peer)

                    save_peer(database, peer_recvd)
                    new_node = Peer(
                        peer_recvd["address"], peer_recvd["public_key"], peer_recvd["name"])

                    '''
                    add new node to list of currently registered nodes
                    '''
                    self.peers.add(new_node)

                    if self.new_join:
                        """
                        only register and request chain if new node
                        """
                        self.transport.write('{}0000{}'.format(
                            identity.sign_data("register"), "register").encode('utf-8'), new_node.address)

                self.new_join = False
                print('\nPeers :\n{}'.format(self.peers))

            return

        '''
        handle comms comming from other peer nodes
        '''
        try:
            recvd_data = datagram.decode().split('0000')
        except Exception as ex:
            print('Failed to decode data : ', ex.__notes__)
        try:
            '''
            verify data before going forward
            '''

            # check with key belonging to addr
            signing_peer = None

            for peer in self.peers:

                if peer.address == addr:
                    signing_peer = peer

            print('Signing peer : ', signing_peer)
            print('recieved data : ', recvd_data)

            verified_data = verify_data(recvd_data[1].encode(
                'utf-8'), eval(recvd_data[0]), rsa.PublicKey.load_pkcs1(signing_peer.pk))

            if verified_data:

                if recvd_data[1] == 'register':
                    """
                    new node requesting chain
                    send chain hashes only
                    """
                    if chain.valid_chain():
                        chain_hashes = '\n'.join(
                            [str(hash_str) for hash_str in chain.get_hashes()])
                        chain2send = str(chain_hashes)
                        signed_chain = identity.sign_data(chain2send)
                        self.transport.write(
                            '{}0000{}0000chain-hashes'.format(signed_chain, chain_hashes).encode('utf-8'), addr)
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
            data2send = 'chain-index-{}'.format(
                self.index_being_validated)
            signed_data = identity.sign_data(data2send)
            signed_data2send = '{}0000{}'.format(
                signed_data, data2send)
            self.transport.write(
                signed_data2send.encode('utf-8'), peer_addr)

        return

    def respondbroadcast_chain_request(self, data, addr):
        chain_index = data[1].split()[-1]
        block_hashes2send = (
            chain.chain[chain_index].hash, chain.chain[chain_index].prev_hash)
        signed_blockhashes = identity.sign_data(block_hashes2send)
        self.transport.write(
            '{}0000{}0000chain-index-{}-hashes-requested'.format(
                signed_blockhashes, block_hashes2send, chain_index),
            addr)
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
                    self.transport.write('{}0000{}'.format(singed_data, data)
                                         .encode('utf-8'), peer)
                for blk in chain.chain:
                    print('\n\n\Block ######\nprev hash : {}\ndata : {}\n hash : {}'.format(
                        blk.prev_hash, blk.data, blk.hash))
            except RuntimeError:
                ignore_error = True

    def validate_peer_chain(self, peer: Peer):
        """
        Validate a Peers` chain based on others
        """
        self.transport.write()

        pass


def main():
    port = randint(1000, 5000)
    reactor.listenUDP(port, Server('192.168.56.1', port))
    reactor.run()


# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
