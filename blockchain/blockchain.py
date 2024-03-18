# Robert Sibanda (robertsibanda20@gmail.com)
# .

import hashlib
from dataclasses import dataclass, field

from .block import Block, HashBlock


# commented
def create_hash(data):
    return hashlib.sha256(f'{data}'.encode('utf-8')).hexdigest()


class Chain:
    
    def __init__(self):
        """
        initilize chain with genesis block, starting point of chain
        """
        self.chain = [self.create_genesis_block()]
    
    def refresh_block(self) -> bool:
        """
        check the valdity of the chain periodically
        or when adding new block depending on what you prefer
        """
        if self.is_valid():
            return True
        return False
    
    def create_genesis_block(self) -> Block:
        blok = Block("0", "0")
        blok.close_block()
        blok.header["hash"] = "0"
        return blok
    
    def create_block_data_hash(self, data):
        hasher = hashlib.sha256()
        [hasher.update(f"{item}".encode('utf-8')) for item in data]
        return hasher.hexdigest()
    
    def add_new_block(self, new_block: Block):
        """
        new block is added ,
        hash calculated using hashlib 'https://hashlib.com'
        linked with previous block`s hash
        """
        new_block.header["prev_hash"] = self.chain[-1].header["hash"]
        new_block.header["hash"] = self.create_block_data_hash(
            [new_block.header["prev_hash"], new_block.header["data_hash"]]
            )
        
        self.chain.append(new_block)
        self.refresh_block()
    
    def get_last_block(self) -> Block:
        """last block os the chain """
        return self.chain[-1]
    
    def get_hashes(self):
        return [(block.header["hash"], block.header["prev_hash"]) for block in self.chain]
    
    def add_transaction_to_block(self, unsaved_block):
        pass
    
    def is_valid(self) -> bool:
        """check validity of the chian"""
        for blck in self.chain:
            if self.chain.index(blck) == 0:
                """ignore the first block"""
                continue
            
            if (self.chain[self.chain.index(blck) - 1].header["hash"]
                    != blck.header["prev_hash"]):
                
                """chech the link between adjuscent blocks"""
                print("Failed between blocks")
                return False
            
            if blck.header["hash"] != self.create_block_data_hash(
                    [blck.header["prev_hash"], blck.header["data_hash"]]
                    ):
                """check the validity of a block`s hash based on data contents"""
                
                print(f"comapring block headers \n{blck.header['hash']}")
                tobehashed = [blck.header["data_hash"], blck.header["prev_hash"]]
                print(self.create_block_data_hash(tobehashed))
                print("Failed in integrity")
                return False
        return True
    
    def get_block(self, block_number):
        return [block for block in self.chain
                if block.header["hash"] == block_number]

    def delete_all_blocks(self):
        pass
    
    
@dataclass
class HashChain:
    chain: set()
    
    def add_block(self, block: HashBlock):
        self.chain.add(block)
    
    def get_subset(self, o_chain) -> bool:
        return set(o_chain.chain).issubset(set(self.chain))
    
    def __le__(self, other):
        if isinstance(other, self.__class__):
            return len(self.chain) <= len(other.chain)
        
    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return len(self.chain) < len(other.chain)
        
        