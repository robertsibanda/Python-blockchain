from pymongo import MongoClient
import rsa


client = MongoClient(host='127.0.0.1', port=27017)
database = client['ehr_chain']

collection = database['users']

person = collection.find_one({'userid' : 'c4ace9bb-50f6-458a-aea8-2fd0a3be5036'})

print(f'Found person: {person}')
public_key = rsa.PublicKey.load_pkcs1_openssl_pem(person['public_key'])

message = 'c4ace9bb-50f6-458a-aea8-2fd0a3be5036'

signature = 'LWepOQHsTvyPIUKdx6XMkttrPOC5NDS/bUPbQr5Dgu/MTV3RuqsTT+o8fb2qUMugHUBoHS7uk2LTKUlbhdmgNvVHxwypbxAqbpv0U2OsaL23KZriNfh79k9LIf6U0G4hD6PmItKh2UCNB6XQ80dhDMzFWAshEnPGZ252pvLN9DM='

rsa.verify(signature, message.encode(), public_key)