import socket
from Block import Block
from BlockChain import Chain
from Peer import Peer
import threading

peers = []



def process_recvd_data(data):
    print(data)


def main():
    sock = socket.socket()
    ip = '127.0.0.1'
    port = 9009
    addr = (ip, port)
    sock.bind(addr)
    sock.listen(2)

    print('Listening at address : {} : {}'.format(ip, port))

    while True:
        client, addr = sock.accept()
        new_peer = Peer(addr)
        for peer in peers:
            if peer.addr == addr:
                return
        peers.append(new_peer)

        data = client.recv(2048)
        threading.Thread(process_recvd_data(data.decode())).start()


threading.Thread(main()).start()
