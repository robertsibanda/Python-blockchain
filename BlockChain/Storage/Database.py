import sys
from pymongo import MongoClient

from BlockChain import BlockChain, create_hash_default
from BlockChain.Block import Block
from BlockChain.Trasanction import Transaction


class Database:
    
    def __init__(self, address, port, database):
        self.client = MongoClient(address, port)
        self.database = self.client[database]
        try:
            self.database.create_collection("blocks")
            self.database.create_collection("users")
        except Exception as ex:
            print("Error refreshing database :", ex)
    
    def lookup_organisation(self, organisation):
        collection = self.database['organisations']
        return collection.find_one({"organisation_id": organisation})
    
    def get_credentials(self, name):
        collection = self.database["users"]
        return collection.find_one({"name": name})
    
    def peer_lookup(self, addr):
        collection = self.database["users"]
        return collection.find_one({"address": addr})
    
    def save_credentials(self, user):
        collection = self.database["users"]
        collection.insert_one(user)
        return
    
    def update_credentials(self, name, user):
        collection = self.database["users"]
        collection.find_one_and_replace({"name": name}, user)
    
    def save_block(self, block: BlockChain.Block):
        collection = self.database["blocks"]
        transactions2save = []
        for transaction in block.transactions:
            transaction2save = {"type": transaction.type, "data": transaction.data,
                                "metadata": transaction.metadata, "hash": transaction.hash
                                }
            transactions2save.append(transaction2save)
        inserted_doc = collection.insert_one(
            {"block_header": block.header, "transactions": transactions2save
             }
            )
        
        return inserted_doc
    
    def lookup_practitioner(self, orgnisation_id, practitioner_id):
        collection = self.database["practitioners"]
        return collection.find_one(
            {'practitioner_id': practitioner_id, "organisation_id": orgnisation_id}
            )
    
    def save_practitioners(self, p_id, details):
        collection = self.database["practitioners"]
        collection.find_one_and_replace({"practitioner_id": p_id}, details)
    
    def load_all_blocks(self, chain: BlockChain.Chain):
        # load previously saved block from the database
        # verify and validate while loading
        collection = self.database["blocks"]
        
        blocks = collection.find()
        for block in blocks:
            # verify block level data
            print("Block############################")
            blk = Block()
            blk.header = block['block_header']
            blk.transactions = []
            
            transactions = block['transactions']
            transaction_hashes = list()
            for transaction in transactions:
                # verify transaction level data
                expected_tr_hash = transaction['hash']
                tr = Transaction(transaction['type'], transaction['data'],
                                 transaction['metadata']
                                 )
                
                print(f"Comparing hashed {expected_tr_hash} and {create_hash_default(tr.data)}",
                      tr.hash == create_hash_default(tr.data)
                      )
                if expected_tr_hash != create_hash_default(tr.data):
                    # throw block invalid exception and delete block data and start again
                    print("Blockchain Transactions Invalid")
                    sys.exit()
                
                transaction_hashes.append(tr.hash)
                blk.transactions.append(tr)
            expected_block_tr_data_hash = block['block_header']['data_hash']
            print(f"comparing {expected_block_tr_data_hash} and {create_hash_default(transaction_hashes)} for {transaction_hashes}")
            if expected_block_tr_data_hash != create_hash_default(transaction_hashes):
                print("Block TransactionHashes mismatch")
                sys.exit()
            chain.chain.append(blk)
    
    def load_peers(self):
        pass
