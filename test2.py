from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

# Load the public key (PEM or DER format)
with open("public_key.pem", "rb") as key_file:
    public_key = RSA.importKey(key_file.read())

# Get the message to be verified
message = "This is the message to be verified".encode()

# Get the signature (assuming it's base64 encoded)
signature = base64.b64decode("your_base64_encoded_signature")

# Create a SHA256 hash object
hasher = SHA256.new(message)

# Create a PKCS1 verifier object using the public key
verifier = PKCS1_v1_5.new(public_key)

try:
  # Attempt to verify the signature
  if verifier.verify(hasher, signature):
    print("The signature is valid!")
  else:
    print("The signature is invalid!")
except (ValueError, TypeError) as e:
  print("An error occurred during verification:", e)
