from pymongo import MongoClient


class Database:

    def __init__(self, address, port, database):
        self.client = MongoClient(address, port)
        self.database = self.client[database]

    def save_block(self, block):
        collections = self.database["blocks"]
        pass

    def get_block(self, details):
        collections = self.database["blocks"]
        pass

    def get_credentials(self):
        collection = self.database["users"]
        return collection.find()

    def save_credentials(self):
        collection = self.database["users"]
        pass


db = Database("localhost", 27017, "jobportal")
print([x for x in db.get_credentials()])
