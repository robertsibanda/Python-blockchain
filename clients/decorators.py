from typing import Callable
from blockchain.storage.object.people import Person, Patient, HealthProfessional


# TODO implement authorisation and authentication


def authenticated(func: Callable):
    def wrapper(*args, **kwargs):
        # make sure the data is from the intended user
        
        return func(*args, **kwargs)
    
    return wrapper


def authorised(func: Callable):
    """
    check if doctor is permitted by patient
    """

    def wrapper(*args, **kwargs):

        database = args[0]
        patient = args[1]['patient']

        patient_data = database.get_patient(patient)

        can_view = patient_data['can_view']
        can_update = patient_data['can_update']

        if func.__name__ == 'insert_record':
           
            #TODO change perm to use userid not pk
            doctor = args[1]['doctor']

            doc_found = False

            if doctor in can_update:
                doc_found = True

            if doc_found is False:
                args = [args,{ "error" : "doctor not allowed"} ]

            return func(*args, **kwargs)

        if func.__name__ == 'view_records':
            doctor = None

            try:
                doctor = args[1]['doctor']
            except KeyError:
                # patient view of information
                return func(*args, **kwargs)

            if doctor in can_view:
                doc_found = True

            if doc_found is False:
                args = [args,{ "error" : "doctor not allowed"} ]
            
            return func(*args, **kwargs)

    return wrapper


def broadcast(func: Callable):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
