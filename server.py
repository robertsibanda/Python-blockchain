# Robert Sibanda (robertsibanda20@gmail.com)
# .

# this is the main node file

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol
from BlockChain.BlockChain import Chain
from BlockChain.Block import Block
from random import randint
from BlockChain.Peer import Peer
from BlockChain.Security.Identity import Identity

chain = Chain([])
identity = Identity()

class Server(DatagramProtocol):

    def __init__(self, host, port):
        self.peers = set()
        self.id = '{}:{}'.format(host, port)
        self.address = None
        self.server = '192.168.56.1', 9009
        print('working on id : ', self.id)

    def startProtocol(self):
        """initialize the connection"""

        self.transport.write('ready'.encode('utf-8'), self.server)

    def verify_data(self, data):
        """
        verifies that the received data is from one of the nodes
        verifies using public key of the stated sender of the data
        """

        return True

    def datagramReceived(self, datagram: bytes, addr):

        """"
        process data received from others peers

        register    - peer registering itself on the network
        peers       - list of all peers that are currently
                       live on the network
        transaction - a data transaction
        status      - chech the status of nodes on the network
        """
        data = datagram.decode('utf-8').split('->')

        self.peers.add(addr)
        if data == 'register':
            ignore_register = True
            return

        elif data[0] == 'peers':
            if data[1] == '':
                return
            for peer in data[1].split('-'):
                new_peer = Peer(eval(peer)[0], eval(peer)[1])
                self.peers.add(new_peer.address)
                self.transport.write("register".encode('utf-8'), new_peer.address)
            print('\nPeers :\n{}'.format(self.peers))
            return

        elif data[0] == 'transaction':
            chain.add_new_block(Block(0, str(data[1]).encode('utf-8')))
            for blk in chain.chain:
                print('\n\n{}\n{}\n{}'.format(blk.prev_hash, blk.data, blk.hash))
            return

        elif data[0] == 'status':
            self.transport.write('alive'.encode('utf-8'), addr)
            return

        else:
            print(data)

        reactor.callInThread(self.send_message)

    def send_message(self):
        while True:
            data = input('::::')
            data2send = identity.sign_data(data)
            chain.add_new_block(Block('0', data))
            try:
                for peer in self.peers:
                    self.transport.write(data2send, peer)
                for blk in chain.chain:
                    print('\n\n\Block ######\nprev hash : {}\ndata : {}\n hash : {}'.format(
                        blk.prev_hash, blk.data, blk.hash))
            except RuntimeError:
                ignore_error = True

    def validate_peer_chain(self, peer):
        """
        Validate a Peers` chain based on others
        """
        pass

    def download_chain(self):
        """
        download a chain from another peers,
        if my chain is invalidated by other peers
        Download the valid chain
        """
        pass

    def upload_chain(self):
        """
        upload a chain to a new Peer or Peer with invalid chain
        """
        pass


def main():
    port = randint(1000, 5000)
    reactor.listenUDP(port, Server('192.168.56.1', port))
    reactor.run()


# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()
