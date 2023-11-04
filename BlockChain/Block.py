class Block:

    def __init__(self, prev_hash, data):
        self.hash = ''
        self.prev_hash = prev_hash
        self.data = data
