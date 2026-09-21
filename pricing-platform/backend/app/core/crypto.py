import json
from functools import lru_cache
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


@lru_cache
def _get_fernet() -> Fernet:
    return Fernet(get_settings().esl_credentials_encryption_key.encode())


def encrypt_credentials(data: dict[str, Any]) -> str:
    """Encrypts a vendor credentials dict for storage in
    ESLIntegration.configuration_encrypted. Rule: credentials are encrypted
    at rest and never returned to the frontend — see
    app/schemas/esl_integration.py's ESLIntegrationOut, which has no field
    for this at all.
    """
    return _get_fernet().encrypt(json.dumps(data).encode()).decode()


def decrypt_credentials(token: str) -> dict[str, Any]:
    try:
        return json.loads(_get_fernet().decrypt(token.encode()).decode())
    except InvalidToken as exc:
        raise ValueError("Stored integration credentials could not be decrypted.") from exc
