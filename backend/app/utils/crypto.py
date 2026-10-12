import base64
import hashlib
import logging

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

logger = logging.getLogger(__name__)

ENCRYPTED_PREFIX = "enc:v1:"


def _fernet() -> Fernet:
    # Derived from SECRET_KEY so no extra secret has to be configured
    digest = hashlib.sha256(
        b"pastexam:gemini-api-key:" + settings.SECRET_KEY.encode()
    ).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str) -> str:
    return ENCRYPTED_PREFIX + _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str | None) -> str | None:
    """Decrypt a stored secret; values stored before encryption are returned as is."""
    if not value:
        return None
    if not value.startswith(ENCRYPTED_PREFIX):
        return value
    try:
        return _fernet().decrypt(value.removeprefix(ENCRYPTED_PREFIX).encode()).decode()
    except InvalidToken:
        # SECRET_KEY changed since it was stored; the user has to enter it again
        logger.warning("Failed to decrypt a stored secret")
        return None
