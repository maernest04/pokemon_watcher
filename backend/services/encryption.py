import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def _get_fernet() -> Fernet:
    secret = os.environ.get("JWT_SECRET", "default-fallback-secret-key-12345")
    # Derive a 32-byte key from the JWT_SECRET
    salt = b"pokemon_watcher_salt" # Static salt is fine here as we are just obfuscating/securing at rest with a system secret
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret.encode()))
    return Fernet(key)

def encrypt_secret(text: str | None) -> str | None:
    if not text:
        return None
    f = _get_fernet()
    return f.encrypt(text.encode()).decode()

def decrypt_secret(token: str | None) -> str | None:
    if not token:
        return None
    f = _get_fernet()
    try:
        return f.decrypt(token.encode()).decode()
    except Exception:
        # If decryption fails (e.g. key changed), return None
        return None
