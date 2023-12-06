import rsa
import hashlib


def verify_data(data, signaure, pk) -> bool:
    """
    verify integrity of data with public key of the sender
    """
    return rsa.verify(data, signaure, pk) == "SHA-256"


def encrypt_data(public_key, data) -> bytes:
    """
    encrypt data to be seen by reciever with their public key
    """
    return rsa.encrypt(data.encode('utf-8'), public_key)
