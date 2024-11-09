
from cryptography.fernet import Fernet
import pickle
import os

# Generate a Fernet key (only once, then save and reuse the key)
def generate_key():
    return Fernet.generate_key()

# Encrypt and save object with Fernet
def save_encrypted_object(data, filename, key):
    fernet = Fernet(key)
    serialized_data = pickle.dumps(data)
    encrypted_data = fernet.encrypt(serialized_data)
    with open(filename, 'wb') as f:
        f.write(encrypted_data)

# Load and decrypt object with Fernet
def load_encrypted_object(filename, key):
    fernet = Fernet(key)
    with open(filename, 'rb') as f:
        encrypted_data = f.read()
    decrypted_data = fernet.decrypt(encrypted_data)
    return pickle.loads(decrypted_data)

ep_save = save_encrypted_object
ep_load = load_encrypted_object