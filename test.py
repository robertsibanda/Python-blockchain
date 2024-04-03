from pymongo import MongoClient

client = MongoClient(host='127.0.0.1', port=27017)
database = client['newdb']

collection = database['patients']

person = collection.insert_one({'name' : 'Robert Sibanda'})
print(person.inserted_id)