from pymongo import MongoClient
import pprint


class Database:

    def __init__(self):
        self.client = MongoClient()
        self.database = self.client["jobportal"]
        print([x['name'] for x in self.database.list_collections()])
        self.collection = self.database["users"]

    def get_data(self):
        return self.collection.find()


db = Database()
