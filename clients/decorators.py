from typing import Callable
from blockchain.storage.object.people import Person, Patient, HealthProfessional


# TODO implement authorisation and authentication


def authenticated(func: Callable):
    def wrapper(*args, **kwargs):
        print("Arguments : ", args)
        return func(*args, **kwargs)
    
    return wrapper


def authorised(func: Callable):
    def wrapper(*args, **kwargs):
        """
        confirm is user is authorised to perfom action
        :param args:
        :param kwargs:
        :return:
        """
        return func(*args, **kwargs)


def broadcast(func: Callable):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
