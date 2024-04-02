from pymongo import MongoClient

client = MongoClient(host='127.0.0.1', port=27017)
database = client['ehr_chain']

collection = database['patients']

person = collection.find_one({ '_id' : '660c607cfab9cdf059e1900c'})
person = collection.find_one_and_modify({}, { '$set' : { "people" : "hello"}})
print(person)