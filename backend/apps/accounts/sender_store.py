"""Trusted backend-only file storage; no OAuth, HTTP, database or provider work."""
from contextlib import contextmanager
from dataclasses import dataclass, field
import errno
import fcntl
import json
import os
from pathlib import Path
import stat
import tempfile
import time
from uuid import UUID, uuid4

from cryptography.fernet import Fernet, InvalidToken


GMAIL_SEND_SCOPE = "https://www.googleapis.com/auth/gmail.send"
MAX_ENCRYPTED_BYTES = 64 * 1024
LOCK_TIMEOUT_SECONDS = 2.0


class SenderStoreError(Exception):
    code = "sender_store_unavailable"
    message = "Sender credential storage is unavailable."

    def __init__(self):
        super().__init__(self.message)


class SenderStoreUnconfigured(SenderStoreError):
    code = "sender_store_unconfigured"
    message = "Sender credential storage is not configured."


class SenderStoreInvalidInput(SenderStoreError):
    code = "sender_store_invalid_input"
    message = "Sender credential input is invalid."


class SenderStoreInvalidRecord(SenderStoreError):
    code = "sender_store_invalid_record"
    message = "Stored sender credentials cannot be read safely."


class SenderStoreClientMismatch(SenderStoreError):
    code = "sender_store_client_mismatch"
    message = "Stored sender credentials belong to another OAuth client."


class SenderStoreConflict(SenderStoreError):
    code = "sender_store_conflict"
    message = "Sender connection changed; read its current state before proceeding."


class SenderStoreBusy(SenderStoreError):
    code = "sender_store_busy"
    message = "Sender credential storage is busy; try again later."


class SenderStoreWriteUncertain(SenderStoreError):
    code = "sender_store_write_uncertain"
    message = "Sender state may have changed; read its current state before proceeding."


def _bounded_string(value, limit):
    if not isinstance(value, str) or not 0 < len(value) <= limit:
        return False
    try:
        value.encode("utf-8")
    except UnicodeError:
        return False
    return True


@dataclass(frozen=True)
class SenderCredential:
    refresh_token: str = field(repr=False)
    client_id: str
    scopes: tuple[str, ...] = (GMAIL_SEND_SCOPE,)

    def __post_init__(self):
        if (not _bounded_string(self.refresh_token, 8192)
                or not _bounded_string(self.client_id, 512)
                or type(self.scopes) is not tuple
                or self.scopes != (GMAIL_SEND_SCOPE,)):
            raise SenderStoreInvalidInput()


@dataclass(frozen=True)
class SenderState:
    generation: UUID | None
    credential: SenderCredential | None = field(repr=False)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate record field.")
        result[key] = value
    return result


class SenderCredentialStore:
    """Short locked reads/writes. Callers never hold a store lock across Google.

    All mutations require the generation from read(); None means no file has
    ever been published. clear() publishes an empty state with a new generation.
    Caller must authorize operations. Objects returned here contain a secret;
    never serialize them to HTTP, log them or dump local variables.
    """

    def __init__(self, directory, encryption_key, *, client_id):
        if not _bounded_string(client_id, 512):
            raise SenderStoreUnconfigured()
        try:
            self._cipher = Fernet(encryption_key)
            self._directory = Path(directory)
            if not self._directory.is_absolute():
                raise ValueError("Absolute private directory required.")
        except (TypeError, ValueError, UnicodeError):
            raise SenderStoreUnconfigured() from None
        self._client_id = client_id
        self._record_path = self._directory / "credentials.enc"
        self._lock_path = self._directory / "credentials.lock"

    @classmethod
    def from_settings(cls, *, client_id):
        # Lazy configuration: missing key does not break account API startup.
        from django.conf import settings
        return cls(settings.GMAIL_CREDENTIAL_STORE_DIR,
                   settings.GMAIL_CREDENTIAL_ENCRYPTION_KEY, client_id=client_id)

    def read(self):
        with self._locked():
            return self._read_locked()

    def replace(self, credential, *, expected_generation):
        if not isinstance(credential, SenderCredential):
            raise SenderStoreInvalidInput()
        if credential.client_id != self._client_id:
            raise SenderStoreClientMismatch()
        return self._mutate(credential, expected_generation)

    def clear(self, *, expected_generation):
        """Local empty marker only; does not revoke anything at Google."""
        return self._mutate(None, expected_generation)

    def _mutate(self, credential, expected_generation):
        if expected_generation is not None and not isinstance(expected_generation, UUID):
            raise SenderStoreInvalidInput()
        with self._locked():
            current = self._read_locked()
            if current.generation != expected_generation:
                raise SenderStoreConflict()
            updated = SenderState(uuid4(), credential)
            self._write_locked(updated)
            return updated

    @staticmethod
    def _check_private(info, mode, *, directory=False):
        kind_ok = stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)
        if (not kind_ok or stat.S_IMODE(info.st_mode) != mode
                or info.st_uid != os.geteuid() or (not directory and info.st_nlink != 1)):
            raise SenderStoreError()

    @contextmanager
    def _locked(self):
        descriptor = None
        try:
            self._directory.mkdir(mode=0o700, exist_ok=True)
            self._check_private(self._directory.lstat(), 0o700, directory=True)
            descriptor = os.open(self._lock_path,
                                 os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                                 0o600)
            self._check_private(os.fstat(descriptor), 0o600)
            deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
            while True:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as error:
                    if error.errno not in (errno.EACCES, errno.EAGAIN):
                        raise
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise SenderStoreBusy() from None
                    time.sleep(min(0.025, remaining))
            yield
        except OSError:
            raise SenderStoreError() from None
        finally:
            if descriptor is not None:
                # Closing also releases flock; never unlink the stable lock file.
                try:
                    os.close(descriptor)
                except OSError:
                    raise SenderStoreError() from None

    def _read_locked(self):
        try:
            descriptor = os.open(self._record_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        except FileNotFoundError:
            return SenderState(None, None)
        with os.fdopen(descriptor, "rb") as source:
            info = os.fstat(source.fileno())
            self._check_private(info, 0o600)
            if info.st_size > MAX_ENCRYPTED_BYTES:
                raise SenderStoreInvalidRecord()
            encrypted = source.read(MAX_ENCRYPTED_BYTES + 1)
        if len(encrypted) > MAX_ENCRYPTED_BYTES:
            raise SenderStoreInvalidRecord()
        try:
            payload = json.loads(self._cipher.decrypt(encrypted), object_pairs_hook=_unique_object)
            if (type(payload) is not dict or set(payload) != {"schema_version", "generation", "credential"}
                    or type(payload["schema_version"]) is not int or payload["schema_version"] != 1
                    or type(payload["generation"]) is not str):
                raise ValueError("Invalid envelope.")
            generation = UUID(payload["generation"])
            if str(generation) != payload["generation"]:
                raise ValueError("Invalid generation.")
            record = payload["credential"]
            credential = None
            if record is not None:
                if (type(record) is not dict or set(record) != {"refresh_token", "client_id", "scopes"}
                        or type(record["scopes"]) is not list):
                    raise ValueError("Invalid credential.")
                credential = SenderCredential(record["refresh_token"], record["client_id"], tuple(record["scopes"]))
        except (InvalidToken, ValueError, TypeError, UnicodeError, RecursionError, SenderStoreInvalidInput):
            raise SenderStoreInvalidRecord() from None
        if credential is not None and credential.client_id != self._client_id:
            raise SenderStoreClientMismatch()
        return SenderState(generation, credential)

    def _write_locked(self, state):
        credential = state.credential
        payload = {"schema_version": 1, "generation": str(state.generation), "credential": None}
        if credential is not None:
            payload["credential"] = {"refresh_token": credential.refresh_token,
                                     "client_id": credential.client_id, "scopes": list(credential.scopes)}
        try:
            encrypted = self._cipher.encrypt(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        except UnicodeError:
            raise SenderStoreInvalidInput() from None
        if len(encrypted) > MAX_ENCRYPTED_BYTES:
            raise SenderStoreInvalidInput()
        temporary_path = None
        published = False
        try:
            descriptor, temporary_path = tempfile.mkstemp(prefix=".credentials-", suffix=".tmp", dir=self._directory)
            with os.fdopen(descriptor, "wb") as destination:
                os.fchmod(destination.fileno(), 0o600)
                destination.write(encrypted)
                destination.flush()
                os.fsync(destination.fileno())
            os.replace(temporary_path, self._record_path)
            published = True
            directory_fd = os.open(self._directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            if published:
                raise SenderStoreWriteUncertain() from None
            raise SenderStoreError() from None
        finally:
            if temporary_path is not None and not published:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    # Only ciphertext could remain; preserve the original failure.
                    pass
