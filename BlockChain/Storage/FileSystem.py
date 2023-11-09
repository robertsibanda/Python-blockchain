from sys import path, getsizeof
from os import mkdir, listdir
import hashlib


class File:

    def __init__(self, name):
        self.name = name
        self.hash = ''

    def save(self):
        pass

    def get(self):
        pass

    def delete(self):
        pass

    def validate(self):
        pass

