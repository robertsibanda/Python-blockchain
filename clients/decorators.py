from typing import Callable
from blockchain.storage.object.people import Person, Patient, HealthProfessional


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

        patient = None
        doctor = None

        try:
            """
            doctor wants to view patient records
            """
            doctor = args[1]['doctor']
            patient = args[1]['patient']
        except KeyError:
            """"
            patient want to view their records
            """
            patient = args[1]['patient']
            doctor = None

        patient_data = database.get_patient(patient)

        if doctor is None:
            if patient_data['userid'] != patient:
                args = [args, {"error": "doctor not allowed"}]
            return func(*args, **kwargs)

        else:
            print(f"Doctor {doctor} viewing patient {patient} data")
            doc_found = False

            try:
                can_view = patient_data['doctor_allowed_view']
            except:
                can_view = []

            print("Can view : ", can_view)

            try:
                can_update = patient_data['doctor_allowed_update']
            except:
                can_update = []

            print("Can update : ", can_update)

            if func.__name__ == 'insert_record':

                doc_found = False

                if doctor in can_update:
                    doc_found = True

                if doc_found is False:
                    args = [args, {"error": "doctor not allowed"}]

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
                    args = [args, {"error": "doctor not allowed"}]

            return func(*args, **kwargs)

    return wrapper


def broadcast(func: Callable):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
