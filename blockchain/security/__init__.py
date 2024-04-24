import hashlib

import rsa


def verify_data(data, signaure, pk) -> bool:
    """
    verify integrity of data with public key of the sender
    """
    # print(f"Public key: {PublicKey._save_pkcs1_pem(pk)}")
    try: rsa.verify(data, signaure, pk) == "SHA-256"; print("verified")
    except: return True


def encrypt_data(public_key, data) -> bytes:
    """
    encrypt data to be seen by reciever with their public key
    """
    return rsa.encrypt(str(data).encode('utf-8'), public_key)


def create_hash_default(data):
    hasher = hashlib.sha256()
    if 'list' in str(type(data)):
        [hasher.update(item.encode('utf-8')) for item in data]
        return hasher.hexdigest()
    return hashlib.sha256(str(data).encode('utf-8')).hexdigest()
