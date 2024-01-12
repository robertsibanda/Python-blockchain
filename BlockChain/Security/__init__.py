import rsa
import hashlib
from rsa import PublicKey, PrivateKey


def verify_data(data, signaure, pk) -> bool:
    """
    verify integrity of data with public key of the sender
    """
    print(f"Verifying data: {data}")
    print(f"Public key: {PublicKey._save_pkcs1_pem(pk)}")
    print(f"Signature: {signaure}")
    return rsa.verify(data, signaure, pk) == "SHA-256"


def encrypt_data(public_key, data) -> bytes:
    """
    encrypt data to be seen by reciever with their public key
    """
    return rsa.encrypt(str(data).encode('utf-8'), public_key)
