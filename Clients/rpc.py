from jsonrpcserver import method, Success, Error, response, request
import time
from BlockChain import BlockChain
from .decorators import authenticated, authorised
from BlockChain.Storage.Object import Organisation
from BlockChain.Storage import Database
from BlockChain.Storage.Object.People import HealthProfessional, Patient


@authenticated
def is_chain_valid(chain):
    return True


def create_new_organisation(db: Database.Database, details):
    #submit a request to create a new organisation
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
        return Success({"Error" : f"Missing request data {ex}"})
    

@authenticated
@authorised
def new_patient(details):
    return Success("patient added")


@authenticated
def add_record(details):
    return Success("record added")


@authenticated
def get_block(block_id, chain):
    for block in chain:
        if block.hash == block_id:
            return Success(block)
