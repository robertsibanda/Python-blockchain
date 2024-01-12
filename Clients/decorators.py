from typing import Callable
from BlockChain.Storage.Object.People import Person, Patient, HealthProfessional


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
