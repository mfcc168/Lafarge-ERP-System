import os

from cryptography.fernet import Fernet

key = str(os.getenv('FERNET_KEY'))
cipher_suite = Fernet(key)


def encrypt_customer_id(customer_id):
    encrypted_id = cipher_suite.encrypt(str(customer_id).encode())
    return encrypted_id.decode()
