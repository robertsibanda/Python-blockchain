import socket

class Peer:

    def __init__(self, addr):
        self.addr = addr
        print('Connected to new peer : {0}  :'
              '  {1}'.format(addr, socket.gethostbyaddr(addr[0])))

    def send_data(self):
        pass

