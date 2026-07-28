import base64
import hashlib
import hmac

from cryptography.fernet import Fernet
from fastapi import Header, HTTPException, status

from .config import get_settings


def _fernet() -> Fernet:
    digest = hashlib.sha256(get_settings().app_secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()


def require_admin(x_admin_password: str = Header(default="")) -> None:
    if not hmac.compare_digest(x_admin_password, get_settings().admin_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid administrator password")

