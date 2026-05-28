"""Node list server — central registry for peer discovery on the blockchain network."""
import json
from typing import Any, Set

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

acceptable_nodes: Set[Any] = set()
leader_node = None


def check_node_acceptability(node: Any) -> bool:
    """Check if a node is acceptable for the network (placeholder).

    Returns:
        Always True.
    """
    return True


def check_alive_status(node: Any) -> bool:
    """Check if a node is still alive (placeholder).

    Returns:
        Always True.
    """
    return True


class Node:
    """A registered node on the network."""

    def __init__(self, addr: str, pk: str, name: str):
        self.name = name
        self.addr = addr
        self.pk = pk


class Server(DatagramProtocol):
    """Twisted UDP server managing peer registration and discovery."""

    def __init__(self):
        self.clients: Set[str] = set()
        self.leader_node = None

    def datagramReceived(self, datagram: bytes, addr: tuple) -> None:
        """Handle incoming datagrams for peer registration and queries."""
        datagram = datagram.decode('utf-8')
        dict_data = json.loads(datagram)

        try:
            if dict_data["status"] == "ready":
                new_client = {
                    "address": addr,
                    "name": dict_data["name"],
                    "public_key": dict_data["pk"]
                }
                if check_node_acceptability(new_client):
                    self.clients.add(json.dumps(new_client))
                    if len(self.clients) == 1:
                        self.leader_node = new_client

            for peer in self.clients:
                all_peers = list(self.clients)
                peer_name_to_remove = [
                    json.loads(x)["name"] for x in self.clients
                    if json.loads(x)["address"] == json.loads(peer)["address"]
                ]
                peer_obj = json.loads(peer)
                peer_to_remove = {"address": peer_obj["address"],
                                  "name": peer_name_to_remove[0]}

                peer_addresses = "::::".join([
                    p for p in all_peers
                    if peer_to_remove['name'] != json.loads(p)['name']
                ])
                peer_recipient = json.loads(peer)
                self.transport.write(
                    f'peers->{peer_addresses}'.encode('utf-8'),
                    tuple(peer_recipient["address"]))

        except KeyError as ex:
            if dict_data.get("request") == "node-leader":
                self.transport.write(
                    f"node-leader->{self.leader_node['name']}")
            print(f"KeyError : {ex}")


if __name__ == '__main__':
    reactor.listenUDP(9009, Server())
    reactor.run()
