# Robert Sibanda (robertsibanda20@gmail.com)
# .

class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.address = self.host, self.port

    def get_address(self):
        return self.address
