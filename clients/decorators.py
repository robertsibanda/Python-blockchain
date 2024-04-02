from typing import Callable
from blockchain.storage.object.people import Person, Patient, HealthProfessional


# TODO implement authorisation and authentication


def authenticated(func: Callable):
    def wrapper(*args, **kwargs):
        print("Arguments : ", args)
        print("kwargs : ", kwargs)
        return func(*args, **kwargs)
    
    return wrapper


def authorised(func: Callable):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper


def broadcast(func: Callable):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
