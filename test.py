from pymongo import MongoClient

client = MongoClient(host='127.0.0.1', port=27017)
database = client['sci4202']

collection = database['patients']

person = collection.find_one({ 'username' : 'lisa'})
print(person == None)