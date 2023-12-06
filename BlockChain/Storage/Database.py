from pymongo import MongoClient

from BlockChain import BlockChain


class Database:

    def __init__(self, address, port, database):
        self.client = MongoClient(address, port)
        self.database = self.client[database]
        try:
            self.database.drop_collection("blocks")
            self.database.drop_collection("users")
        except Exception as ex:
            print("Error refreshing database :", ex)

        self.database.create_collection("blocks")
        self.database.create_collection("users")

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
            transaction2save = {
                "type": transaction.type,
                "data": transaction.data,
                "metadata": transaction.metadata,
                "hash": transaction.hash
            }
            transactions2save.append(transaction2save)
        inserted_doc = collection.insert_one({"block_header": block.header,
                                              "transactions": transactions2save
                                              })

        return inserted_doc
