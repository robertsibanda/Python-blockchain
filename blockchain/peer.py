from dataclasses import dataclass
from typing import Any, Optional, Set


@dataclass
class Peer:
    """A network peer node with address, public key, and name."""
    address: str
    pk: str
    name: str

    def __hash__(self):
        return hash(f"{self.address, self.pk, self.name}")


def save_peer(database, peer: Any) -> None:
    """Save a peer's credentials to the database."""
    database.save_credentials(peer)


def verify_peer() -> None:
    """Placeholder for peer verification logic."""
    pass


def peer_exists(peers: Set[Peer], peer: Peer) -> bool:
    """Check if a peer (by name) already exists; if so, update its address."""
    peer_found = False
    for _peer in peers:
        if _peer.name == peer.name:
            peer_found = True
            peers.remove(_peer)
            peers.add(peer)
    return peer_found


class Peers:
    """A collection of Peer objects with lookup by address."""

    def __init__(self):
        self.peers: Set[Peer] = set()

    def lookup(self, addr: str) -> Optional[Peer]:
        """Find a peer by its address."""
        for peer in self.peers:
            if peer.address == addr:
                return peer
        return None
