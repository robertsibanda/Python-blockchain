# Robert Sibanda (robertsibanda20@gmail.com)
# .

class Peer:
    def __init__(self, addr, public_key, name):
        self.address = addr
        self.pk = public_key
        self.name = name

    def get_address(self):
        return self.address


def save_peer(database, peer):
    database.save_credentials(peer)


def verify_peer():
    pass


def peer_exists(peers, addr) -> bool:
    for peer in peers:
        if peer.address == addr:
            return True
    return False


class Peers:

    def __init__(self):
        self.peers = set()

    def lookup(self, addr):
        for peer in self.peers:
            if peer.address == addr:
                return peer
