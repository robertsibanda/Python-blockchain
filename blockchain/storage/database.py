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


    def find_user_byid(self, userid):
        found_user = None
        collection = self.database['users']
        found_user = collection.find_one({ 'userid' : userid})
        return found_user

    
    def create_temporary_permission(self, perm_data):
        collection = self.database['temp_permissions']
        collection.insert_one({ 'perm' : perm_data})
        return 

    def get_temp_permissions(self, doctor, patient):
        collection = self.database['temp_permissions']
        return collection.find_one({ 'doctor' : doctor, 'patient' : patient})

    def delete_temp_permission(self, doc, patient):
        collection = self.database['temp_permissions']
        collection.find_one_and_delete({ 'doctor' : doc, 'patient' : patient})
        return


    def get_close_appointments(self, user, date):
        appointments = []
        
        user_appointments = []
        
        user_type = user['user_type']

        collection = self.database['appointments']
        
        if date == 'all':
            appointments = collection.find({ user_type : user['userid']})
            for app in appointments:
                user_appointments.append(app)
        else:
            appointments = collection.find({ user_type : user['userid']})
            user_appointments = [app for app in appointments if (int(date) - int(app['date_key'])) < 10]
        
        for app in user_appointments:
            app['_id'] = None
            

        print("appointments 2 : ", user_appointments)

        return user_appointments
        
    def get_user_appointments(self, user, date):

        appointments = []
        
        user_appointments = []
        
        user_type = user['user_type']

        collection = self.database['appointments']
        
        if date == 'all':
            appointments = collection.find({ user_type : user['userid']})
            for app in appointments:
                user_appointments.append(app)
        else:
            appointments = collection.find({ user_type : user['userid']})
            user_appointments = [app for app in appointments if int(date) == int(app['date_key'])]
        
        for app in user_appointments:
            app['_id'] = None
            

        print("appointments 2 : ", user_appointments)

        return user_appointments

    def get_appointment(self, doctor, patient, date_key, time):
        collection = self.database['appointments']
        appointment = collection.find_one({ 'doctor' : doctor, 
            'patient' : patient, 'date_key' : date_key, 'time' : time})

        return appointment

    def update_appointment(self, appointment):
        collection  = self.database['appointments']
        appointment = collection.find_one_and_update({ 
            'doctor' : appointment['doctor'], 'patient' : appointment['patient'], 
            'date' : appointment['date'], 'time' : appointment['time']},
             {  '$set' : {'approved' : appointment['approved'], 'rejected' : appointment['rejected']}})
        return 

    def save_appointment(self, data):
        collection = self.database['appointments']
        collection.insert(data)
        return


    def get_patient_records(self, userid, record_type):
        # get patient records from databases
        # records based on categories : allegies, labresults, medicines
        collection = self.database['patients']
        patient = collection.find_one({ 'userid' : userid})
        records = None
        
        try:
            records = patient[record_type]
        except KeyError:
            records = []
        return records


    def search_my_doctor(self, userid):
        # lookup user who i gave permission 
        my_docs = []
        docs = self.search_user('', 'doctor', userid)

        for doc in docs:
            if doc['view'] is True or doc['update'] is True:
                my_docs.append(doc)
        return my_docs


    def search_my_patient(self, userid):
        # lookup users who gave me permission in the database
        my_patients = []
        patients = self.search_user('', 'patient', userid)
        for patient in patients:
            if doc['view'] is True or doc['update'] is True:
                my_patients.append(patient)
        return my_patients


    def search_user(self, infor, user_type, userid):
        # get a user where info is a sub-string of identifying information
        # user id form request body

        collection = self.database['users']

        found_users = collection.find({ 'usertype' : user_type })

        users_to_return = []
        
        if user_type == 'patient':
            # searching for patient
            for patient in found_users:
                can_view  = False
                can_update = False

                try:
                    if userid in patient['doctor_allowed_view']:
                        can_view = True
                except Exception as ex:
                    print("Error : " , ex)
                    doc_not_found = True

                #check if doctor is allowed to update records_data
                try:
                    if userid in patient['doctor_allowed_update']:
                        can_view = True
                except Exception as ex:
                    print("Error : " , ex)
                    doc_not_found = True

                users_to_return.append({
                    'fullname' : patient['fullname'],
                    'gender' : patient['gender'],
                    'userid' : patient['userid'],
                    'contact' : patient['contact'],
                    'user type' : patient['usertype'],
                    'view' : can_view,
                    'update' : can_update,
                })

        elif user_type == 'doctor':
            # searching for doctor
            patient = collection.find_one({ 'userid' : userid })
            
            for doc in found_users:
                can_view =  False
                can_update = False

                # check if doctor is allowed to view records
                try:
                    if doc['userid'] in patient['doctor_allowed_view']:
                        can_view = True
                except Exception as ex:
                    print("Error : " , ex)
                    doc_not_found = True

                #check if doctor is allowed to update records_data
                try:
                    if doc['userid'] in patient['doctor_allowed_update']:
                        can_update = True
                except Exception as ex:
                    print("Error : " , ex)
                    doc_not_found = True

                users_to_return.append({
                    'fullname' : doc['fullname'],
                    'gender' : doc['gender'],
                    'userid' : doc['userid'],
                    'contact' : doc['contact'],
                    'user type' : doc['usertype'],
                    'organisation' : doc['organisation'],
                    'occupation' : doc['occupation'],
                    'bio' : doc['bio'],
                    'view' : can_view,
                    'update' : can_update,
                })

        return users_to_return


    def save_patient(self, pk, userid):
        collection = self.database["patients"]
        return collection.insert_one(
            {'public_key' : pk,
            'userid' : userid,
             'permissions' : [], 'records' : []})


    def get_patient(self, id):
        collection = self.database['patients']
        return collection.find_one({ 'userid' : id})


    def save_doctor(self, data):
        collection = self.database['doctor']
        return collection.insert_one(data)

    def get_doctor(self, id):
        collection = self.database['doctor']
        return collection.find_one({ 'userid' : id })


    def update_permissions(self, userid, doctor, perm, perm_code):
        collection = self.database["patients"]
        patient = collection.find_one({'userid' : userid})

        perm_dir = f'doctor_allowed_{perm}'
        
        found_doctors = None
        
        new_lis = []

        if perm_code is False:
            allowed = patient[perm_dir]
            allowed = allowed.remove(doctor)
            collection.find_one_and_update({ 'userid' : userid },
                { '$set' : {perm_dir: allowed}})
            return
        
        try:
            found_doctors = patient[perm_dir]
        except KeyError:
            found_doctors = None

        if found_doctors is None:
            new_lis = [doctor]
        else:
            new_lis = patient[perm_dir]

            new_lis.append(doctor)
        
        print('Adding permission')
        permed_patient = collection.find_one_and_update({'userid': userid}, 
            { '$set' : {perm_dir: new_lis}})
        print('patient updated : ' , permed_patient)

        return 


    def update_records(self, userid, record_type, record_data):
        collection = self.database['patients']
        patient = collection.find_one({ 'userid': userid })

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

        collection.find_one_and_update({ 'userid': userid}, 
            { '$set' : { record_type : new_lis}})

        return

    
    def save_credentials(self, user):
        collection = self.database["users"]
        collection.insert_one(user)
        return
        
    
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
    

    def get_all_blocks(self):
        collection = self.database["blocks"]
        return collection.find({})
