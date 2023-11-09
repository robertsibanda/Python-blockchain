# Robert Sibanda (robertsibanda20@gmail.com)
# .

class Peer:
    def __init__(self, addr, public_key, name):
        self.address = addr
        self.pk = public_key
        self.name = name

    def get_address(self):
        return self.address


class Peers:

    def __init__(self):
        self.peers = set()

    def lookup(self, addr):
        for peer in self.peers:
            if peer.address == addr:
                return peer
