from jsonrpcserver import Success, Error
import datetime
from dataclasses import asdict
from uuid import uuid4

from blockchain import blockchain
from blockchain.trasanction import Transaction
from blockchain.storage import database
from blockchain.storage.onchain import save_transaction
from blockchain.storage.object.organisation import Org
from blockchain.storage.object.people import HealthProfessional, Patient, Person

from .decorators import authenticated, authorised, broadcast


# TODO make methods save only reference to blockchain data 
# TODO -> transactionid and blockid not all record data


def get_block_data(chain: blockchain.Chain, block_number):
    # get the transactions and header of block using block_id
    try:
        block = chain.get_block(block_number)
        if block is not None:
            return Success(block)
    except IndexError:
        return Error({"message": f"block {block_number} not found"})


@authorised
def is_chain_valid(chain: blockchain.Chain):
    return chain.is_valid()


@authorised
@broadcast
def create_new_organisation(db: database.Database, details) -> Transaction:
    # submit a request to create a new organisation
    pass


def register_new_practitioner(db: database.Database, details) -> Transaction:
    """
    Register a new practioner in the chain
    :param db: ehr_chain database
    :param details: credentials for new practioner
    :return:
    """
    
    try:
        # print("Signup details : ", details)
        organisation_id = details['organisation_id']
        practitioner_id = details['practitioner_id']
        
        organisation = Org(db, organisation_id)
        
        practitioner_found = organisation.get_practitioner(practitioner_id)
        
        # print('Practitoner : ' , practitioner_id)
        # print('Practitoner : ' , organisation.get_practitioner(practitioner_id))
        if organisation.get_practitioner(practitioner_id) is None:
            return Success({"Error": "You are not able to register under this organisation"})
        
        if practitioner_found["pk"] != "":
            return Success({"Error": "Practioner is already registered"})
        
        hp_name = details['practitioner_name']
        hp_role = details['practitioner_role']
        hp_pk = details['practitioner_pk']
        health_professional = HealthProfessional(
            hp_name, organisation_id, hp_role, hp_pk, practitioner_id)
        health_professional.save(db)
        
        return 'acc_created'
    except KeyError as ex:
        return Success({"Error": f"Missing request data {ex}"})

@authenticated
def update_permissions(db: database.Database, details) -> Transaction:

    perms_data = details

    """patient updates permissions
    # -> give caregivers permissions to update records
    # -> give researchers permissions to use data in researches

    perms_data
        [...,doctor_x, doctor_y]
    """
    transaction = Transaction(type="permission update", 
        data={'doctor' : perms_data['doctor'], 
        'patient' : perms_data['patient'] }, 
        metadata=str(datetime.datetime.today()), hash='')
        
    save_transaction(db, transaction)

    return transaction

def create_account(db: database.Database, details) -> Transaction:
    
    # change jsobOject to dict
    userdata  = details

    user_type = None
    
    person_id = uuid4()

    userdata['userid'] = person_id
    
    # save new user only with public_key
    if 'public_key' in userdata.keys():
        if db.find_user(userdata['public_key']) == None:
            person = db.save_person(userdata)
        else:
            return { 'failed' : 'user already exists'}

    if 'patient' in userdata.values():
        # create account for Patient
        user_type = 'patient'

    if 'doctor' in userdata.values():
        # create account for doctor
        user_type = 'doctor'

    transction = Transaction(type="account init", 
        data={'public_key' : userdata['public_key'], 'userid' : person_id, 'user_type':  user_type}, 
        metadata=['created account', str(datetime.datetime.today().date())], 
        hash='')
    save_transaction(db, transction)

    return transction

@authenticated
def find_person(db: database.Database, details):
    # not a recorded transaction
    search_string = details['search_string']

    users = db.find_user(search_string)
    
    return users


@authorised
def view_records(db: database.Database, details) -> Transaction:

    # view records of a patient
    records_data = details
    transaction = Transaction(type="log", data=records_data, 
        metadata=['records view', str(datetime.datetime.today().date())], hash='')
    return transaction

@authorised
def insert_record(db: database.Database, details) -> Transaction:

    try:
        if details['error']:
            return details
    except KeyError:
        ingore=  True

    record_data = details['record']
    record_type = details['type']
    patient = details['patient']
    doctor = details['doctor']

    transaction  = Transaction(type="record", 
        data={ 'type' : record_type, 'data' : record_data},
        metadata={ 'patient' : patient, 'doctor' : doctor, 
        'date': str(datetime.datetime.today().date())}, hash='')

    save_transaction(db, transaction)
    return transaction