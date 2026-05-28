import hashlib
from typing import Any, List, Union

import rsa


def verify_data(data: bytes, signature: bytes, pk: rsa.PublicKey) -> bool:
    """Verify the integrity of data using the sender's public key.

    Args:
        data: The original data that was signed.
        signature: The RSA signature to verify.
        pk: The public key of the signer.

    Returns:
        True if the signature is valid, False otherwise.
    """
    try:
        return rsa.verify(data, signature, pk) == "SHA-256"
    except Exception:
        return False


def encrypt_data(public_key: rsa.PublicKey, data: Any) -> bytes:
    """Encrypt data with the receiver's public key.

    Args:
        public_key: The RSA public key of the intended recipient.
        data: The data to encrypt.

    Returns:
        Encrypted bytes.
    """
    return rsa.encrypt(str(data).encode('utf-8'), public_key)


def create_hash_default(data: Union[str, List[str]]) -> str:
    """Compute a SHA-256 hex digest of the given data (string or list of strings).

    Args:
        data: A string or list of strings to hash.

    Returns:
        The hexadecimal SHA-256 digest.
    """
    hasher = hashlib.sha256()
    if isinstance(data, list):
        [hasher.update(item.encode('utf-8')) for item in data]
        return hasher.hexdigest()
    return hashlib.sha256(str(data).encode('utf-8')).hexdigest()
