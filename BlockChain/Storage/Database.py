from pymongo import MongoClient


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
