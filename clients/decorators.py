from typing import Callable
from blockchain.storage.object.people import Person, Patient, HealthProfessional


# TODO implement authorisation and authentication


def authenticated(func: Callable):
    def wrapper(*args, **kwargs):
        # make sure the data is from the intended user
        return func(*args, **kwargs)
    
    return wrapper


def authorised(func: Callable):

    def wrapper(*args, **kwargs):

        if func.__name__ == 'insert_record':
            """
            check if doctor is permitted by patient
            """

            print("Args : ", args[1])

            doctor = args[1]['doctor']

            database = args[0]

            patient = args[1]['patient']

            doctor_pk = database.get_doctor(doctor)['public_key']
            patient_data = database.get_patient(patient)

            permissioned_doctors = patient_data['permissions']

            doc_found = False

            if doctor in permissioned_doctors:
                doc_found = True

            if doc_found is False:
                args = [args,{ "error" : "doctor not allowed"} ]

            return func(*args, **kwargs)
    
    return wrapper


def broadcast(func: Callable):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
