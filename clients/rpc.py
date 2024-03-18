from jsonrpcserver import Success, Error

from blockchain import blockchain
from blockchain.storage import database
from blockchain.storage.object.organisation import Org
from blockchain.storage.object.people import HealthProfessional
from .decorators import authenticated, authorised, broadcast


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
def create_new_organisation(db: database.Database, details):
    # submit a request to create a new organisation
    pass


def register_new_practitioner(db: database.Database, details):
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
    

@authorised
@broadcast
def new_patient(db: database.Database ,details):
    # [firstname, lastname, dob, gender, idnmber, addr, phone]
    # image later

    for key, value in details.items():
        pass # TODO 1
    return Success("patient added")



@authenticated
@broadcast
def add_record(details):
    return Success("record added")
