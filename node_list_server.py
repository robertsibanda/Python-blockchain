from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import rsa
from rsa import PublicKey


class Node:

    def __init__(self, addr, pk, name):
        self.name = name
        self.addr = addr
        self.pk = pk


class Server(DatagramProtocol):

    def __init__(self):
        self.clients = set()

    def datagramReceived(self, datagram, addr):
        datagram = datagram.decode('utf-8')

        self.clients.add(str({"address": addr, "public_key": PublicKey._save_pkcs1_pem(eval(
            datagram)["pk"]), "name": eval(datagram)["name"]}))

        peers = "000000".join([str(x) for x in self.clients])

        for peer in self.clients:
            self.transport.write(
                'peers->{}'.format(peers).encode('utf-8'), (eval(peer)["address"]))

        print("\n\nClients  :::::::::::::::")
        for peer in self.clients:
            print('\n')
            print(peer)


if __name__ == '__main__':
    reactor.listenUDP(9009, Server())
    reactor.run()
