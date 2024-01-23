from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from random import randint
from blockchain.block import Block
from blockchain.blockchain import Chain


chain = Chain([])


class Client(DatagramProtocol):

    def __init__(self, host, port):

        self.id = '{}:{}'.format(host, port)
        self.address = None
        self.server = '196.220.120.222', 9009
        print('working on id : ', self.id)

    def startProtocol(self):
        self.transport.write('ready'.encode('utf-8'), self.server)

    def datagramReceived(self, datagram, addr):

        datagram = datagram.decode()
        if addr == self.server:
            print("Choose a device to connect\n", datagram)
            self.address = input("Write host : "), int(input("Write port : "))
            reactor.callInThread(self.send_message)
        else:
            chain.add_new_block(Block('0', datagram))
            for blk in chain.chain:
                print('\n\nBlock ######\nprev hash : {}\ndata : {}\n hash : {}'.format(
                    blk.prev_hash, blk.data, blk.hash))

    def send_message(self):
        while True:
            data = input('::::')
            chain.add_new_block(Block('0', data))
            self.transport.write(data.encode('utf-8'), self.address)
            chain.chain[-1].data = 'fake data'
            for blk in chain.chain:
                print('\n\n\Block ######\nprev hash : {}\ndata : {}\n hash : {}'.format(
                    blk.prev_hash, blk.data, blk.hash))


if __name__ == '__main__':
    port = randint(1000, 5000)
    reactor.listenUDP(port, Client('196.220.120.222', port))
    reactor.run()
