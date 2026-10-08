"""Internal committed attempt lifecycle. No HTTP, Google calls or file-store I/O."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import re
import secrets
from uuid import UUID, uuid4

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.models import Session
from django.db import connection, transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare

from .models import OAuthConnectionAttempt, User
from .oauth_pkce import code_challenge, decrypt_verifier, encrypt_verifier, generate_verifier


ATTEMPT_LIFETIME = timedelta(minutes=10)
STATE_PATTERN = re.compile(r"\A[0-9a-f]{64}\Z")
SESSION_PATTERN = re.compile(r"\A[a-z0-9]{32}\Z")


class InvalidOAuthAttempt(Exception):
    code = "invalid_oauth_attempt"

    def __init__(self):
        super().__init__("This connection attempt is invalid or no longer available.")


class OAuthAttemptInputError(Exception):
    code = "oauth_attempt_invalid_input"

    def __init__(self):
        super().__init__("Connection attempt input is invalid.")


class OAuthAttemptTransactionError(Exception):
    code = "oauth_attempt_transaction_required"

    def __init__(self):
        super().__init__("Connection attempts require an independent committed transaction.")


@dataclass(frozen=True)
class IssuedOAuthAttempt:
    id: UUID
    state: str = field(repr=False)
    expires_at: datetime
    code_challenge: str
    code_challenge_method: str = "S256"


@dataclass(frozen=True)
class ClaimedOAuthAttempt:
    id: UUID
    user_id: UUID
    client_id: str
    expected_generation: UUID | None
    code_verifier: str = field(repr=False)


def _digest(value):
    return hashlib.sha256(value.encode("ascii")).hexdigest()


def _require_independent_transaction():
    # Explicit check also rejects TestCase's implicit transaction, which durable
    # atomic blocks otherwise special-case. Use TransactionTestCase for callers.
    if connection.in_atomic_block or not connection.get_autocommit():
        raise OAuthAttemptTransactionError()


def _validate_context(user_id, session_key, client_id):
    if (not isinstance(user_id, UUID) or not isinstance(session_key, str)
            or SESSION_PATTERN.fullmatch(session_key) is None):
        raise InvalidOAuthAttempt()
    if not isinstance(client_id, str) or not 0 < len(client_id) <= 512:
        raise OAuthAttemptInputError()
    try:
        client_id.encode("utf-8")
    except UnicodeError:
        raise OAuthAttemptInputError() from None


def _lock_identity(user_id, session_key):
    """User -> Session -> Attempt lock order; no authentication/session mutation."""
    try:
        user = User.objects.select_for_update().get(pk=user_id)
        session = Session.objects.select_for_update().get(session_key=session_key)
    except (User.DoesNotExist, Session.DoesNotExist):
        raise InvalidOAuthAttempt() from None
    now = timezone.now()  # Sample after acquiring the identity locks.
    if not (user.is_active and user.is_email_verified and user.is_superuser) or session.expire_date <= now:
        raise InvalidOAuthAttempt()
    data = session.get_decoded()
    if not isinstance(data, dict):
        raise InvalidOAuthAttempt()
    auth_hash = data.get(HASH_SESSION_KEY)
    if (data.get(SESSION_KEY) != str(user.pk)
            or data.get(BACKEND_SESSION_KEY) != "apps.accounts.authentication.VerifiedAccountBackend"
            or data.get(BACKEND_SESSION_KEY) not in settings.AUTHENTICATION_BACKENDS
            or not isinstance(auth_hash, str)
            or not constant_time_compare(auth_hash, user.get_session_auth_hash())):
        raise InvalidOAuthAttempt()
    return user


def create_oauth_attempt(user_id, session_key, client_id, expected_generation):
    """Return a secret only after commit; never supersede on invalid identity."""
    _require_independent_transaction()
    _validate_context(user_id, session_key, client_id)
    if expected_generation is not None and not isinstance(expected_generation, UUID):
        raise OAuthAttemptInputError()
    with transaction.atomic(durable=True):
        user = _lock_identity(user_id, session_key)
        now = timezone.now()
        if not Session.objects.filter(session_key=session_key, expire_date__gt=now).exists():
            raise InvalidOAuthAttempt()
        OAuthConnectionAttempt.objects.filter(user=user, claimed_at=None, superseded_at=None).update(
            superseded_at=now, encrypted_pkce_verifier=None)
        raw_state = secrets.token_hex(32)
        attempt_id = uuid4()
        verifier = generate_verifier()
        ciphertext = encrypt_verifier(verifier, attempt_id, _digest(raw_state))
        attempt = OAuthConnectionAttempt.objects.create(
            id=attempt_id, encrypted_pkce_verifier=ciphertext,
            user=user, state_digest=_digest(raw_state), session_digest=_digest(session_key),
            client_id=client_id, expected_generation=expected_generation,
            created_at=now, expires_at=now + ATTEMPT_LIFETIME)
        result = IssuedOAuthAttempt(attempt.pk, raw_state, attempt.expires_at, code_challenge(verifier))
    return result


def claim_oauth_attempt(raw_state, user_id, session_key, client_id):
    """Commit one accepted claim. Any later external failure cannot unclaim it."""
    _require_independent_transaction()
    _validate_context(user_id, session_key, client_id)
    if not isinstance(raw_state, str) or STATE_PATTERN.fullmatch(raw_state) is None:
        raise InvalidOAuthAttempt()
    with transaction.atomic(durable=True):
        user = _lock_identity(user_id, session_key)
        try:
            attempt = OAuthConnectionAttempt.objects.select_for_update().get(
                state_digest=_digest(raw_state), user=user)
        except OAuthConnectionAttempt.DoesNotExist:
            raise InvalidOAuthAttempt() from None
        now = timezone.now()  # Expiry checked after any attempt-lock wait too.
        if (attempt.claimed_at is not None or attempt.superseded_at is not None
                or now >= attempt.expires_at or now < attempt.created_at
                or not constant_time_compare(attempt.session_digest, _digest(session_key))
                or attempt.client_id != client_id):
            raise InvalidOAuthAttempt()
        # Recheck session expiry against the final claim time, not an earlier read.
        if not Session.objects.filter(session_key=session_key, expire_date__gt=now).exists():
            raise InvalidOAuthAttempt()
        verifier = decrypt_verifier(attempt.encrypted_pkce_verifier, attempt.pk, attempt.state_digest)
        attempt.claimed_at = now
        attempt.encrypted_pkce_verifier = None
        attempt.save(update_fields=["claimed_at", "encrypted_pkce_verifier"])
        result = ClaimedOAuthAttempt(attempt.pk, user.pk, attempt.client_id, attempt.expected_generation, verifier)
    return result
