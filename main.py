import socket
from Block import Block
from BlockChain import Chain
from Peer import Peer
import threading


peers = []


def process_recvd_data(data):
    print(data)


def handle_client_connection(client, addr):
    try:
        while True:
            data = client.recv(2048)
            if not data:
                continue
            client.send('received'.encode('ascii'))
            print('{} -> {}'.format(addr, data))
    except:
        client.close()


def main():
    sock = socket.socket()
    ip = '192.168.56.1'
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

        # threading.Thread(handle_client_connection(client, addr)).start()
        th = threading.Thread(handle_client_connection(client, addr))
        th.start()

    sock.close()


threading.Thread(main()).start()
