from jsonrpcserver import method, Success, Error, response, request
import time
from blockchain import BlockChain
from .decorators import authenticated, authorised
from blockchain.storage.object import organisation
from blockchain.storage import database
from blockchain.storage.object.people import HealthProfessional, Patient


def get_block_data(chain: BlockChain.Chain, block_number):
    # get the transactions and header of block using block_id
    try:
        block = chain.get_block(block_number)
        if block is not None:
            return Success(block)
    except IndexError:
        return Error({"message": f"block {block_number} not found"})


@authorised
def is_chain_valid(chain):
    return True


@authorised
def create_new_organisation(db: Database.Database, details):
    # submit a request to create a new organisation
    pass


def register_new_practitioner(db: Database.Database, details):
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
        
        organisation = Organisation.Org(db, organisation_id)
        
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
    

@authorised
def new_patient(details):
    return Success("patient added")


@authenticated
def add_record(details):
    return Success("record added")
