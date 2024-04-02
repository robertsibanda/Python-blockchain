import sys
from pymongo import MongoClient
from blockchain import blockchain
from blockchain.block import Block
from blockchain.trasanction import Transaction

# TODO create method for indexing and looking up transaction details


class Database:
    
    def __init__(self, address, port, database):
        self.client = MongoClient(host=address, port=port)
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
    
    def save_person(self, userdata):
        collection = self.database["users"]
        return collection.insert_one(userdata)

    def find_user(self, key):
        collection = self.database['users']
        return collection.find_one({ 'public_key' : key})

    def save_patient(self, patient_data):
        collection = self.database["patients"]
        return collection.insert_one({'public_key' : patient_data,
             'permissions' : [], 'records' : []})

    def save_doctor(self, doctor_data):
        collection = self.database['doctor']
        return collection.insert_one({ 'public_key' : doctor_data})

    def update_permissions(self, pk, perm, doctor):
        collection = self.database["patients"]
        patient = collection.find_one({ 'public_key': pk})

        # check if doctor already existed, case of update
        # TODO permission architecture
        doc_found = False
        return 

    def update_records(self, patient, record_type, record_data):
        collection = self.database['patients']
        patient = collection.find_one({ public_key: patient })

        old_records = patient[record_type]
        collection.find_one_and_update({ public_key: patient}, 
            { record_type : old_records.append(record_data)})
        return

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
    
    def save_block(self, block: blockchain.Block):
        collection = self.database["blocks"]

        if collection.find_one({'block_header' : block.header}):
            print('Transaction already exists')
            return False
            
        transactions2save = []

        for transaction in block.transactions:
            transaction2save = {"type": transaction.type, "data": transaction.data,
                "metadata": transaction.metadata, "hash": transaction.hash}
            
            transactions2save.append(transaction2save)

        inserted_doc = collection.insert_one({"block_header": block.header, 
            "transactions": transactions2save})

        return True
    
    def lookup_practitioner(self, orgnisation_id, practitioner_id):
        collection = self.database["practitioners"]
        return collection.find_one(
            {'practitioner_id': practitioner_id, "organisation_id": orgnisation_id})
    
    def save_practitioners(self, p_id, details):
        collection = self.database["practitioners"]
        collection.find_one_and_replace({"practitioner_id": p_id}, details)
    
    def get_all_blocks(self):
        collection = self.database["blocks"]
        
        return collection.find({})
    
    def load_peers(self):
        pass
