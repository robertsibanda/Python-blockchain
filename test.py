from pymongo import MongoClient
import rsa


client = MongoClient(host='127.0.0.1', port=27017)
database = client['ehr_chain']

collection = database['users']

people = collection.find(
    {'userid': 'cdd36b47-524d-4f04-9e76-2b94e09ad5d6'})

collection = database['patients']
patients = collection.find({})

patients = [x for x in patients]

doctor = "58102008-32b5-47cf-9136-010eb5c1d094"

for person in people:
    user_data = person

    print(user_data['userid'])

    single_patien = [p for p in patients if p['userid'] == user_data['userid']]

    patient_index = patients.index(single_patien[0])

    patient_data = patients[patient_index]

    user_data['can_update'] = doctor in patient_data['doctor_allowed_update']
    print(f"Doctor {doctor} allowed update {user_data['can_update']}")
