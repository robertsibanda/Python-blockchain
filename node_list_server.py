from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from rsa import PublicKey
import threading

accepable_nodes = set()


def check_node_acceptability(node):
    # check if node does not already exist on the network with different address
    # check if the node is authentic
    return True


def check_alive_status(node):
    # check that the nodes are still alive
    # and update the node-list if there are any changes
    return True


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
        
        dict_data = eval(datagram)
        
        try:
            # data from node is dictionary
            
            if dict_data["status"] == "ready":
                """
                message recvd from a new node ready to enter the network
                """
                
                new_client = {"address": addr, "name": dict_data["name"],
                              "public_key": PublicKey._save_pkcs1_pem(dict_data["pk"])}
                
                if check_node_acceptability(new_client):
                    # add new node if it is acceptable
                    self.clients.add(str(new_client))
            
            peers = "000000".join([str(x) for x in self.clients])
            
            for peer in self.clients:
                all_peers = list(self.clients)
                
                print(f"List of all peers to be sent: {all_peers}")
                
                # find the name of the peer to be removed
                # peer to be removed is the one to receive list of peers
                peer_name_to_remove = [eval(x)["name"] for x in self.clients if
                                       eval(x)["address"] == eval(peer)["address"]]
                
                print(f"peer name to be removed {peer_name_to_remove}")
                # set the value of the peer to be removed
                peer_to_remove = {"address": eval(peer)["address"],
                                  "name": peer_name_to_remove[0]}
                
                print(f"peer to be removed: {peer_to_remove}")
                
                # create a list of other peers leaving the peer ot receive the datagram
                peer_addresses = "::::".join(
                    [str(eval(peer)) for peer in all_peers if
                     eval(peer)["address"] != peer_to_remove["address"]]
                    )
                
                print(f"peers to be send {peer_addresses}")
                
                print(f"Peer to recieve datagram {eval(peer)['address']}")
                # send the remaining peers to the node
                self.transport.write(f'peers->{peer_addresses}'.encode('utf-8'),
                                     (eval(peer)["address"])
                                     )
        except KeyError:
            # data from mobile client is list
            
            if dict_data["request"] == "node-request":
                # a mobile client requesting a node
                pass
            
            if dict_data["request"] == "node-report":
                # report a node not responding
                pass
            pass


if __name__ == '__main__':
    # the node-list-server must always run on port 9009
    reactor.listenUDP(9009, Server())
    #status_server_thread = threading.Thread(target=check_alive_status)
    #status_server_thread.start()
    reactor.run()
