from cryptography.fernet import Fernet
import rsa
from ecdsa import SigningKey, VerifyingKey, keys


def verify_data(data, signaure, pk) -> bool:
    """
    verify integrity of data with public key of the sender
    """
    return rsa.verify(data, signaure, pk) == "SHA-256"


def encrypt_data(public_key, data) -> bytes:
    """
    encrypt data to be seen by reciever with their public key
    """
    pass


class Identity:
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.load_public_key()
        self.load_private_key()

    def sign_data(self, data):
        signed_data = rsa.sign(data.encode(
            'utf-8'), self.private_key, 'SHA-256')
        return signed_data

    def create_new_keys(self) -> None:
        """
        create new keys for new node
        """
        print("Generating new keys .. first time launch\nPlease wait a moment ....")
        new_public_key, new_private_key = rsa.newkeys(2000)

        private_key_file = open("private.pem", 'wb')
        public_key_file = open("public.pem", "wb")

        self.private_key = new_private_key.save_pkcs1("PEM")
        self.public_key = new_public_key.save_pkcs1("PEM")
        private_key_file.write(self.private_key)
        public_key_file.write(self.public_key)

        private_key_file.close()
        public_key_file.close()

        print("Generating keys done, do not share keys with anyone")
        return

    def load_private_key(self) -> None:
        """
        load private key from saved file
        """
        try:
            with open("private.pem", 'rb+') as key_file:
                private_key_data = key_file.read()
            self.private_key = rsa.PrivateKey.load_pkcs1(private_key_data)
        except FileNotFoundError:
            self.create_new_keys()

    def load_public_key(self):
        """
        load public key from saved file
        """
        try:
            with open("public.pem", 'rb+') as key_file:
                public_key_data = key_file.read()
            self.public_key = rsa.PublicKey.load_pkcs1(public_key_data)
        except FileNotFoundError:
            if self.private_key is None:
                self.create_new_keys()
            else:
                return "Public key is missing"

    def derypt_data(self, data):
        return rsa.decrypt(data, self.private_key).decode('utf-8')
