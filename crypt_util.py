from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Function to derive a key from a string (using PBKDF2 for example)
def derive_key_from_string(secret_string, salt):
    # Using PBKDF2 for key derivation
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # The length of the derived key in bytes
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(secret_string.encode())

# Encryption function
def encrypt(data, secret_string):
    salt = os.urandom(16)  # Random salt for key derivation
    key = derive_key_from_string(secret_string, salt)
    cipher = Cipher(algorithms.AES(key), modes.GCM(salt), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
    return base64.b64encode(salt + ciphertext)  # Returning the result in base64

# Decryption function
def decrypt(encrypted_data, secret_string):
    encrypted_data = base64.b64decode(encrypted_data)
    salt = encrypted_data[:16]  # Extract salt
    ciphertext = encrypted_data[16:]  # Extract ciphertext
    key = derive_key_from_string(secret_string, salt)
    
    cipher = Cipher(algorithms.AES(key), modes.GCM(salt), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
    return decrypted_data.decode()
