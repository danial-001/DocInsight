"""Bounded PKCE secrets for trusted backend callers; no persistence or provider I/O."""
import base64
import hashlib
import json
import re
import secrets
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


class OAuthPKCEConfigurationError(Exception):
    code = "oauth_pkce_unconfigured"

    def __init__(self):
        super().__init__("Connection attempt encryption is not configured.")


class InvalidOAuthPKCE(Exception):
    code = "invalid_oauth_pkce"

    def __init__(self):
        super().__init__("Connection attempt proof is invalid.")


def _fernet():
    key = getattr(settings, "GMAIL_CREDENTIAL_ENCRYPTION_KEY", None)
    try:
        if not isinstance(key, str) or len(key) != 44:
            raise ValueError
        raw = base64.b64decode(key.encode("ascii"), altchars=b"-_", validate=True)
        if len(raw) != 32 or base64.urlsafe_b64encode(raw).decode("ascii") != key:
            raise ValueError
        return Fernet(key.encode("ascii"))
    except (ValueError, UnicodeError):
        raise OAuthPKCEConfigurationError() from None


def _base64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def generate_verifier():
    return _base64url(secrets.token_bytes(32))


def code_challenge(verifier):
    if not isinstance(verifier, str) or re.fullmatch(r"[A-Za-z0-9._~-]{43,128}", verifier) is None:
        raise InvalidOAuthPKCE()
    return _base64url(hashlib.sha256(verifier.encode("ascii")).digest())


def _validate_context(attempt_id, state_digest):
    if (not isinstance(attempt_id, UUID) or not isinstance(state_digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", state_digest) is None):
        raise InvalidOAuthPKCE()


def encrypt_verifier(verifier, attempt_id, state_digest):
    _validate_context(attempt_id, state_digest)
    code_challenge(verifier)
    record = {"schema_version": 1, "attempt_id": str(attempt_id),
              "state_digest": state_digest, "verifier": verifier}
    return _fernet().encrypt(json.dumps(record, separators=(",", ":")).encode("ascii")).decode("ascii")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def decrypt_verifier(ciphertext, attempt_id, state_digest):
    _validate_context(attempt_id, state_digest)
    cipher = _fernet()  # Configuration failure is distinct, but never contains key material.
    try:
        if not isinstance(ciphertext, str) or not 0 < len(ciphertext) <= 1024:
            raise ValueError
        plaintext = cipher.decrypt(ciphertext.encode("ascii"))
        if len(plaintext) > 512:
            raise ValueError
        record = json.loads(plaintext.decode("utf-8"), object_pairs_hook=_unique_object)
        if (not isinstance(record, dict)
                or set(record) != {"schema_version", "attempt_id", "state_digest", "verifier"}
                or type(record["schema_version"]) is not int or record["schema_version"] != 1
                or record["attempt_id"] != str(attempt_id)
                or record["state_digest"] != state_digest):
            raise ValueError
        code_challenge(record["verifier"])
        return record["verifier"]
    except (ValueError, UnicodeError, InvalidToken, RecursionError, InvalidOAuthPKCE):
        raise InvalidOAuthPKCE() from None
