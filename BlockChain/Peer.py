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


def peer_exists(peers, peer) -> bool:
    # check whether the peer (name) is not already in the list
    # change the address of the peer if it already exists
    return False


class Peers:

    def __init__(self):
        self.peers = set()

    def lookup(self, addr):
        for peer in self.peers:
            if peer.address == addr:
                return peer
