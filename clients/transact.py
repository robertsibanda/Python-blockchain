from clients.rpc import create_account, view_records, update_permissions,  \
    insert_record, find_person, find_my_docs, Response, book_appointment, get_user_appointments, update_user_appointment, get_close_appointments
from jsonrpcserver import Success
from blockchain.trasanction import Transaction
from blockchain.storage.database import Database

database = Database()

def signup(headers):
    return create_account(database, headers)

def update_records(headers):
    return insert_record(database, headers)

def view_health_records(headers):
    response = view_records(database, headers)
    if isinstance(response, Response):
        return Success({"success": response.response})
    else:
        return response


def update_data_permissions(headers):
    return update_permissions(database, headers)


def get_my_doctors(headers):
    return find_my_docs(database, headers)
 
 
def search_person(headers):
    result = find_person(database, headers)

    if len(result) == 0:
        return Success({'error': 'no user found'})

    else:
        return Success({'success': result})


def create_appointment(headers):
    result = book_appointment(database, headers)
    return result


def get_appointments(headers):
    result = get_user_appointments(database, headers)
    return result


def get_upcoming_appointments(headers):
    result = get_close_appointments(database, headers)
    return Success({"success": result})


def update_appointment(headers):
    result = update_user_appointment(database, headers)

    if isinstance(result, Transaction):
        return result
    else:
        return Success(result)

    return Success({"success": "appointment updated"})


def account_history(headers):
    return Success({"success": "history not yet available"})


def temporary_permission(headers):
    return Success({'success': "permission added"})


def delete_account(headers):
    return