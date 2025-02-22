import os
import pickle
from cryptography.fernet import Fernet
import traceback

def save_encrypted_object(data, filename, key):
    """
    Encrypts and saves an object to a file using Fernet symmetric encryption.

    :param data: The Python object to save.
    :param filename: Path to the file where the encrypted object will be saved.
    :param key: The encryption key (bytes) used for Fernet.
    """
    fernet = Fernet(key)
    serialized_data = pickle.dumps(data)  # Serialize the object
    encrypted_data = fernet.encrypt(serialized_data)  # Encrypt the serialized data

    with open(filename, 'wb') as f:
        f.write(encrypted_data)

def load_encrypted_object(filename, key):
    """
    Loads and decrypts an object from an encrypted file using Fernet symmetric encryption.

    :param filename: Path to the file where the encrypted object is stored.
    :param key: The decryption key (bytes) used for Fernet.
    :return: The decrypted and deserialized Python object.
    """
    fernet = Fernet(key)

    with open(filename, 'rb') as f:
        encrypted_data = f.read()  # Read encrypted data

    decrypted_data = fernet.decrypt(encrypted_data)  # Decrypt the data
    return pickle.loads(decrypted_data)  # Deserialize into a Python object

# Short aliases for convenience
ep_save = save_encrypted_object
ep_load = load_encrypted_object
