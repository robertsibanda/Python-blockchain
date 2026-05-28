import rsa


class Identity:
    """Manages RSA key pair for signing, verification, encryption, and decryption."""

    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.load_public_key()
        self.load_private_key()

    def sign_data(self, data) -> bytes:
        """Sign data with the private key using SHA-256.

        Args:
            data: The data to sign.

        Returns:
            The RSA signature bytes.
        """
        return rsa.sign(str(data).encode('utf-8'), self.private_key, 'SHA-256')

    def create_new_keys(self) -> None:
        """Generate a new RSA key pair (2048-bit) and save to PEM files."""
        print("Generating new keys .. first time launch\nPlease wait a moment ....")
        new_public_key, new_private_key = rsa.newkeys(2048)

        self.private_key = new_private_key.save_pkcs1("PEM")
        self.public_key = new_public_key.save_pkcs1("PEM")

        with open("private.pem", 'wb') as private_key_file:
            private_key_file.write(self.private_key)
        with open("public.pem", "wb") as public_key_file:
            public_key_file.write(self.public_key)

        print("Generating keys done, do not share keys with anyone")

    def load_private_key(self) -> None:
        """Load the private key from private.pem; generate keys if file not found."""
        try:
            with open("private.pem", 'rb+') as key_file:
                private_key_data = key_file.read()
            self.private_key = rsa.PrivateKey.load_pkcs1(private_key_data)
        except FileNotFoundError:
            self.create_new_keys()

    def load_public_key(self) -> str | None:
        """Load the public key from public.pem; generate keys if not found."""
        try:
            with open("public.pem", 'rb+') as key_file:
                public_key_data = key_file.read()
            self.public_key = rsa.PublicKey.load_pkcs1(public_key_data)
        except FileNotFoundError:
            if self.private_key is None:
                self.create_new_keys()
            else:
                return "Public key is missing"
        return None

    def decrypt_data(self, data: bytes) -> str:
        """Decrypt data using the private key.

        Args:
            data: The encrypted data bytes.

        Returns:
            The decrypted UTF-8 string.
        """
        return rsa.decrypt(data, self.private_key).decode('utf-8')
