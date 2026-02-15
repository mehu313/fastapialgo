import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("BROKER_ENCRYPTION_KEY")

if not SECRET_KEY:
    raise Exception("BROKER_ENCRYPTION_KEY not set in .env")

cipher = Fernet(SECRET_KEY)


def encrypt_data(data: str) -> str:
    return cipher.encrypt(data.encode()).decode()


def decrypt_data(data: str) -> str:
    return cipher.decrypt(data.encode()).decode()
