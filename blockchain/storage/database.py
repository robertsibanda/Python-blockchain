import sys
from pymongo import MongoClient
from bson.objectid import ObjectId

from blockchain import blockchain
from blockchain.block import Block
from blockchain.trasanction import Transaction


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
        # create new user account with only public key
        collection = self.database["users"]
        return collection.insert_one(userdata)
    
    def find_user(self, pk):
        # get user with public_key
        collection = self.database['users']
        return collection.find_one({ 'public_key' : pk })
    
    def search_user(self, infor, userid):
        # get a user where infor is a substring of identifying information
        # user id form request body

        collection = self.database['users']
        found_users = collection.find({})
        users_to_return = []

        for user in found_users:
            if infor in user['fullname'] \
                or infor in user['phone number'] \
                    or infor in user['natinal id']:
                
                my_patient = False
                collection = self.database['patient']
                patient_infor = collection.find_one({ 'userid' : userid})
                    # user is a patient
                if patient_infor is not None:
                    if userid in patient_infor['permissions']:
                        my_patient = True
                else:
                    my_patient = False

                users_to_return.append({
                    'fullname' : user['fullname'],
                    'gender' : user['gender'],
                    'contact' : user['phone number'],
                    'user type' : user['usertype'],
                    'allow edit' : my_patient
                })

        return users_to_return

    def save_patient(self, patient_data):
        collection = self.database["patients"]
        return collection.insert_one({'public_key' : patient_data,
             'permissions' : [], 'records' : []})

    def get_patient(self, id):
        collection = self.database['patients']
        return collection.find_one({ 'userid' : id})

    def save_doctor(self, doctor_data):
        collection = self.database['doctor']
        return collection.insert_one({ 'public_key' : doctor_data})

    def get_doctor(self, id):
        collection = self.database['doctor']
        return collection.find_one({ 'userid' : id })

    def update_permissions(self, id, doctor):
        collection = self.database["patients"]

        patient = collection.find_one({'_id' : ObjectId(id)})

        new_lis = []


        try:
            if doctor in patient['permissions']:
                return { "error" : "doctor already alloweed"}
        except TypeError:
            error = 'no permissions found for patient'

        try:
            if patient['permissions'] == None:      
                new_lis = [doctor]
        except TypeError:
            error = "no permissions found for patient"

        if len(patient['permissions'])  == 0:
            new_lis = [doctor]

        else:
            new_lis = patient['permissions']

            new_lis.append(doctor)
        
        collection.find_one_and_update({'_id': ObjectId(id)}, 
            { '$set' : {'permissions': new_lis}})

        return 

    def update_records(self, id, record_type, record_data):
        collection = self.database['patients']
        patient = collection.find_one({ '_id': ObjectId(id) })

        if patient == None:
            return { "failed " : "patient does not exist"}
        old_records = []

        try:
            old_records = patient[record_type]
        except KeyError:
            ingore = True

        new_lis = []

        if old_records == None or len(old_records)  == 0:      
            new_lis = [record_data]

        else:
            new_lis = old_records
            new_lis.append(record_data)

        collection.find_one_and_update({ '_id': ObjectId(id)}, 
            { '$set' : { record_type : new_lis}})

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
            
            transaction2save = {"type": transaction.type, 
                "data": transaction.data,"metadata": transaction.metadata, 
                "hash": transaction.hash}
            
            transactions2save.append(transaction2save)

        inserted_doc = collection.insert_one({"block_header": block.header, 
            "transactions": transactions2save})

        return True
    
    def lookup_practitioner(self, orgnisation_id, practitioner_id):

        collection = self.database["practitioners"]
        return collection.find_one({'practitioner_id': practitioner_id, 
            "organisation_id": orgnisation_id})
    
    def save_practitioners(self, p_id, details):
        collection = self.database["practitioners"]
        collection.find_one_and_replace({"practitioner_id": p_id}, details)
    
    def get_all_blocks(self):
        collection = self.database["blocks"]
        
        return collection.find({})