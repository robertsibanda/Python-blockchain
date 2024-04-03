# Robert Sibanda (robertsibanda20@gmail.com)
# .

from dataclasses import dataclass


@dataclass()
class Peer:
    address: str
    pk: str
    name: str
    
    def __hash__(self):
        return hash(f"{self.address, self.pk, self.name}")


def save_peer(database, peer):
    database.save_credentials(peer)


def verify_peer():
    pass


def peer_exists(peers, peer) -> bool:
    # check whether the peer (name) is not already in the list
    # change the address of the peer if it already exists
    peer_found = False
    for _peer in peers:
        if _peer.name == peer.name:
            peer_found = True 
            # update new peer details
            peers.remove(_peer)
            peers.add(peer)
    return peer_found


class Peers:
    
    def __init__(self):
        self.peers = set()
    
    def lookup(self, addr):
        for peer in self.peers:
            if peer.address == addr:
                return peer
