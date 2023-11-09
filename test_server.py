from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor


class Server(DatagramProtocol):

    def __init__(self):
        self.clients = set()

    def datagramReceived(self, datagram, addr):
        datagram = datagram.decode('utf-8')

        peers = "-".join([str(x) for x in self.clients])
        self.transport.write(
            'peers->{}'.format(peers).encode('utf-8'), addr)

        self.clients.add({address: "addr", "public_key": eval(
            datagram)["pk"], "name": eval(datagram)["name"]})


if __name__ == '__main__':
    reactor.listenUDP(9009, Server())
    reactor.run()
