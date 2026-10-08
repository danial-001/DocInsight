"""Synthetic secrets in temporary directories; no real credentials/provider calls."""
import fcntl
import json
import multiprocessing
import os
from pathlib import Path
import stat
import tempfile
import time
import traceback
from unittest.mock import patch
from uuid import uuid4

from cryptography.fernet import Fernet
from django.test import SimpleTestCase, override_settings

from apps.accounts.sender_store import (
    GMAIL_SEND_SCOPE, MAX_ENCRYPTED_BYTES, SenderCredential, SenderCredentialStore,
    SenderStoreBusy, SenderStoreClientMismatch, SenderStoreConflict, SenderStoreError,
    SenderStoreInvalidInput, SenderStoreInvalidRecord, SenderStoreUnconfigured,
    SenderStoreWriteUncertain,
)


CLIENT_ID = "synthetic-client.apps.example.invalid"
SYNTHETIC_TOKEN = "synthetic-refresh-secret-not-a-google-credential"


def _hold_lock(directory, ready, release):
    with open(Path(directory) / "credentials.lock", "r+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        ready.set()
        if not release.wait(8):
            raise RuntimeError("Synthetic test coordination timed out.")


def _compete_write(directory, key, barrier, outcomes):
    store = SenderCredentialStore(directory, key, client_id=CLIENT_ID)
    state = store.read()
    barrier.wait(timeout=8)
    try:
        store.replace(SenderCredential(SYNTHETIC_TOKEN, CLIENT_ID), expected_generation=state.generation)
        outcomes.put("saved")
    except SenderStoreConflict:
        outcomes.put("conflict")


def _stale_write(directory, key, ready, proceed, outcomes):
    store = SenderCredentialStore(directory, key, client_id=CLIENT_ID)
    state = store.read()
    ready.set()
    if not proceed.wait(8):
        raise RuntimeError("Synthetic test coordination timed out.")
    try:
        store.replace(SenderCredential(SYNTHETIC_TOKEN, CLIENT_ID), expected_generation=state.generation)
        outcomes.put("saved")
    except SenderStoreConflict:
        outcomes.put("conflict")


class SenderStoreTests(SimpleTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="docinsight-synthetic-sender-")
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name)
        self.directory = self.parent / "store"
        self.key = Fernet.generate_key()
        self.store = self.new_store()
        self.credential = SenderCredential(SYNTHETIC_TOKEN, CLIENT_ID)
        self.record_path = self.directory / "credentials.enc"

    def new_store(self, *, key=None, client_id=CLIENT_ID):
        return SenderCredentialStore(self.directory, self.key if key is None else key, client_id=client_id)

    def seed(self):
        return self.store.replace(self.credential, expected_generation=None)

    def put_encrypted_json(self, payload):
        if not self.directory.exists():
            self.store.read()
        plaintext = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.record_path.write_bytes(Fernet(self.key).encrypt(plaintext))
        self.record_path.chmod(0o600)

    def assert_unchanged_failure(self, exception, operation):
        previous = self.record_path.read_bytes()
        with self.assertRaises(exception):
            operation()
        self.assertEqual(self.record_path.read_bytes(), previous)

    def test_missing_state_creates_private_directory_and_stable_lock_only(self):
        state = self.store.read()
        self.assertIsNone(state.generation)
        self.assertIsNone(state.credential)
        self.assertFalse(self.record_path.exists())
        self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.directory / "credentials.lock").stat().st_mode), 0o600)

    def test_roundtrip_new_instance_and_no_plaintext_secret_on_disk_or_repr(self):
        state = self.seed()
        self.assertEqual(self.new_store().read(), state)
        self.assertEqual(state.credential.refresh_token, SYNTHETIC_TOKEN)
        self.assertNotIn(SYNTHETIC_TOKEN, repr(self.credential))
        self.assertNotIn(SYNTHETIC_TOKEN, repr(state))
        self.assertNotIn(self.key.decode(), repr(self.store))
        self.assertEqual(stat.S_IMODE(self.record_path.stat().st_mode), 0o600)
        for path in self.directory.iterdir():
            data = path.read_bytes()
            self.assertNotIn(SYNTHETIC_TOKEN.encode(), data)
            self.assertNotIn(self.key, data)

    def test_replacement_rotates_generation_and_retains_lock_inode(self):
        first = self.seed()
        inode = (self.directory / "credentials.lock").stat().st_ino
        replacement = SenderCredential("synthetic-replacement", CLIENT_ID)
        second = self.new_store().replace(replacement, expected_generation=first.generation)
        self.assertNotEqual(first.generation, second.generation)
        self.assertEqual(self.store.read().credential, replacement)
        self.assertEqual((self.directory / "credentials.lock").stat().st_ino, inode)

    def test_clear_keeps_empty_marker_and_rejects_stale_restore(self):
        first = self.seed()
        cleared = self.new_store().clear(expected_generation=first.generation)
        self.assertIsNone(cleared.credential)
        self.assertIsNotNone(cleared.generation)
        self.assertNotEqual(cleared.generation, first.generation)
        self.assertEqual(self.new_store().read(), cleared)
        self.assert_unchanged_failure(SenderStoreConflict, lambda: self.store.replace(
            self.credential, expected_generation=first.generation))
        self.assert_unchanged_failure(SenderStoreConflict, lambda: self.store.replace(
            self.credential, expected_generation=None))
        reconnected = self.store.replace(self.credential, expected_generation=cleared.generation)
        self.assertNotEqual(reconnected.generation, cleared.generation)

    def test_clearing_absent_state_still_prevents_initial_old_callback(self):
        cleared = self.store.clear(expected_generation=None)
        self.assertIsNotNone(cleared.generation)
        self.assert_unchanged_failure(SenderStoreConflict, lambda: self.store.replace(
            self.credential, expected_generation=None))

    def test_stale_clear_cannot_remove_new_connection(self):
        first = self.seed()
        second = self.store.replace(self.credential, expected_generation=first.generation)
        self.assert_unchanged_failure(SenderStoreConflict, lambda: self.store.clear(
            expected_generation=first.generation))
        self.assertEqual(self.store.read(), second)

    def test_missing_or_invalid_key_is_unconfigured_without_filesystem_changes(self):
        for key in [None, "", "bad-key", b"bad-key", "\ud800"]:
            with self.subTest(key_type=type(key).__name__), self.assertRaises(SenderStoreUnconfigured):
                SenderCredentialStore(self.directory, key, client_id=CLIENT_ID)
        self.assertFalse(self.directory.exists())

    def test_settings_factory_is_optional_and_does_not_use_django_secret_key(self):
        with override_settings(GMAIL_CREDENTIAL_STORE_DIR=self.directory,
                               GMAIL_CREDENTIAL_ENCRYPTION_KEY="", SECRET_KEY=self.key.decode()):
            with self.assertRaises(SenderStoreUnconfigured):
                SenderCredentialStore.from_settings(client_id=CLIENT_ID)
        with override_settings(GMAIL_CREDENTIAL_STORE_DIR=self.directory,
                               GMAIL_CREDENTIAL_ENCRYPTION_KEY=self.key.decode()):
            self.assertIsNone(SenderCredentialStore.from_settings(client_id=CLIENT_ID).read().generation)

    def test_bad_directory_or_client_configuration_fails_safely(self):
        for directory, client_id in [("relative", CLIENT_ID), (self.directory, ""), (self.directory, "x" * 513)]:
            with self.subTest(directory_kind=type(directory).__name__), self.assertRaises(SenderStoreUnconfigured):
                SenderCredentialStore(directory, self.key, client_id=client_id)

    def test_wrong_key_never_overwrites_existing_record(self):
        state = self.seed()
        wrong_key_store = self.new_store(key=Fernet.generate_key())
        for operation in [wrong_key_store.read, lambda: wrong_key_store.clear(expected_generation=state.generation),
                          lambda: wrong_key_store.replace(self.credential, expected_generation=state.generation)]:
            self.assert_unchanged_failure(SenderStoreInvalidRecord, operation)

    def test_tamper_and_empty_file_are_invalid_not_missing(self):
        state = self.seed()
        encrypted = self.record_path.read_bytes()
        for data in [b"", b"not-an-encrypted-record", encrypted[:-5] + b"AAAAA"]:
            self.record_path.write_bytes(data)
            self.assert_unchanged_failure(SenderStoreInvalidRecord, self.store.read)
            self.assert_unchanged_failure(SenderStoreInvalidRecord, lambda: self.store.replace(
                self.credential, expected_generation=state.generation))

    def test_oversized_ciphertext_is_rejected_before_decryption(self):
        self.store.read()
        self.record_path.write_bytes(b"x" * (MAX_ENCRYPTED_BYTES + 1))
        self.record_path.chmod(0o600)
        with patch("apps.accounts.sender_store.Fernet.decrypt", side_effect=AssertionError("Must not decrypt")):
            self.assert_unchanged_failure(SenderStoreInvalidRecord, self.store.read)

    def test_invalid_envelopes_credentials_and_duplicate_json_keys_are_rejected(self):
        envelope = {"schema_version": 1, "generation": str(uuid4()), "credential": None}
        credential = {"refresh_token": SYNTHETIC_TOKEN, "client_id": CLIENT_ID, "scopes": [GMAIL_SEND_SCOPE]}
        invalid = [[], {}, {**envelope, "schema_version": True}, {**envelope, "schema_version": 2},
                   {**envelope, "generation": None}, {**envelope, "generation": "invalid"},
                   {**envelope, "extra": "forbidden"}, {**envelope, "credential": []},
                   {**envelope, "credential": {**credential, "access_token": "not-allowed"}},
                   {**envelope, "credential": {**credential, "refresh_token": ""}},
                   {**envelope, "credential": {**credential, "refresh_token": "x" * 8193}},
                   {**envelope, "credential": {**credential, "client_id": "x" * 513}},
                   {**envelope, "credential": {**credential, "scopes": ["unapproved-scope"]}},
                   {**envelope, "credential": {**credential, "scopes": GMAIL_SEND_SCOPE}},
                   b'{"schema_version":1,"schema_version":1}', b"invalid-json", b"\xff",
                   b"[" * 2000 + b"]" * 2000,
                   {**envelope, "credential": {**credential, "refresh_token": "\ud800"}}]
        for index, payload in enumerate(invalid):
            with self.subTest(case=index):
                self.put_encrypted_json(payload)
                self.assert_unchanged_failure(SenderStoreInvalidRecord, self.store.read)
                self.assert_unchanged_failure(SenderStoreInvalidRecord, lambda: self.store.clear(expected_generation=None))

    def test_client_mismatch_blocks_read_replace_clear_without_mutation(self):
        state = self.seed()
        other_client = self.new_store(client_id="other-synthetic-client")
        for operation in [other_client.read, lambda: other_client.clear(expected_generation=state.generation),
                          lambda: other_client.replace(SenderCredential("synthetic-other", "other-synthetic-client"),
                                                       expected_generation=state.generation)]:
            self.assert_unchanged_failure(SenderStoreClientMismatch, operation)
        self.assert_unchanged_failure(SenderStoreClientMismatch, lambda: self.store.replace(
            SenderCredential("synthetic-other", "other-synthetic-client"), expected_generation=state.generation))

    def test_invalid_mutation_input_does_not_write(self):
        for refresh_token, client_id, scopes in [("", CLIENT_ID, (GMAIL_SEND_SCOPE,)),
                ("x" * 8193, CLIENT_ID, (GMAIL_SEND_SCOPE,)), (SYNTHETIC_TOKEN, "", (GMAIL_SEND_SCOPE,)),
                (SYNTHETIC_TOKEN, CLIENT_ID, []), (SYNTHETIC_TOKEN, CLIENT_ID, ("unapproved",))]:
            with self.assertRaises(SenderStoreInvalidInput):
                SenderCredential(refresh_token, client_id, scopes)
        with self.assertRaises(SenderStoreInvalidInput):
            self.store.replace({}, expected_generation=None)
        with self.assertRaises(SenderStoreInvalidInput):
            self.store.clear(expected_generation="not-a-uuid-object")
        self.assertFalse(self.directory.exists())

    def test_error_tracebacks_do_not_echo_synthetic_secret_or_key(self):
        self.put_encrypted_json(b'{"secret":"' + SYNTHETIC_TOKEN.encode() + b'",invalid}')
        try:
            self.store.read()
        except SenderStoreInvalidRecord as error:
            formatted = "".join(traceback.format_exception(error))
            self.assertNotIn(SYNTHETIC_TOKEN, formatted)
            self.assertNotIn(self.key.decode(), formatted)
            self.assertEqual(error.code, "sender_store_invalid_record")
        else:
            self.fail("Malformed record accepted")

    def test_insecure_existing_directory_is_not_silently_chmodded(self):
        self.directory.mkdir(mode=0o755)
        with self.assertRaises(SenderStoreError):
            self.store.read()
        self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o755)

    def test_insecure_existing_files_are_preserved(self):
        state = self.seed()
        for path in [self.record_path, self.directory / "credentials.lock"]:
            path.chmod(0o644)
            previous = self.record_path.read_bytes()
            try:
                with self.assertRaises(SenderStoreError):
                    self.store.clear(expected_generation=state.generation)
                self.assertEqual(self.record_path.read_bytes(), previous)
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o644)
            finally:
                path.chmod(0o600)

    def test_symlink_root_lock_and_record_are_rejected(self):
        real = self.parent / "external"
        real.mkdir(mode=0o700)
        self.directory.symlink_to(real, target_is_directory=True)
        with self.assertRaises(SenderStoreError):
            self.store.read()
        self.directory.unlink()
        self.store.read()
        target = real / "untouched"
        target.write_bytes(b"synthetic external file")
        for name in ["credentials.enc", "credentials.lock"]:
            path = self.directory / name
            if path.exists():
                path.unlink()
            path.symlink_to(target)
            try:
                with self.assertRaises(SenderStoreError):
                    self.store.read()
                self.assertEqual(target.read_bytes(), b"synthetic external file")
            finally:
                path.unlink()

    def test_nonregular_record_is_rejected_without_blocking(self):
        self.store.read()
        os.mkfifo(self.record_path, 0o600)
        with self.assertRaises(SenderStoreError):
            self.store.read()

    def test_hardlinked_record_is_rejected(self):
        self.seed()
        os.link(self.record_path, self.parent / "linked-record")
        self.assert_unchanged_failure(SenderStoreError, self.store.read)

    def test_failure_before_replace_preserves_old_bytes_and_cleans_temporary_ciphertext(self):
        state = self.seed()
        for target in ["os.replace", "os.fsync", "tempfile.mkstemp"]:
            with self.subTest(failure=target), patch("apps.accounts.sender_store." + target,
                                                   side_effect=OSError("synthetic failure")):
                self.assert_unchanged_failure(SenderStoreError, lambda: self.store.replace(
                    self.credential, expected_generation=state.generation))
            self.assertEqual(list(self.directory.glob(".credentials-*.tmp")), [])

    def test_directory_sync_failure_after_replace_reports_uncertain_not_rollback(self):
        state = self.seed()
        replacement = SenderCredential("synthetic-new-value", CLIENT_ID)
        with patch("apps.accounts.sender_store.os.fsync", side_effect=[None, OSError("synthetic directory failure")]):
            with self.assertRaises(SenderStoreWriteUncertain):
                self.store.replace(replacement, expected_generation=state.generation)
        current = self.new_store().read()
        self.assertNotEqual(current.generation, state.generation)
        self.assertEqual(current.credential, replacement)
        self.assert_unchanged_failure(SenderStoreConflict, lambda: self.store.replace(
            self.credential, expected_generation=state.generation))

    def test_lock_is_released_after_validation_error(self):
        self.seed()
        self.record_path.write_bytes(b"invalid ciphertext")
        with self.assertRaises(SenderStoreInvalidRecord):
            self.store.read()
        descriptor = os.open(self.directory / "credentials.lock", os.O_RDWR)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(descriptor)


class SenderStoreProcessTests(SimpleTestCase):
    """Spawned OS processes with independent descriptors; not simulated locks."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="docinsight-synthetic-process-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / "store"
        self.key = Fernet.generate_key()
        self.store = SenderCredentialStore(self.directory, self.key, client_id=CLIENT_ID)
        self.store.read()
        self.context = multiprocessing.get_context("spawn")

    def start_worker(self, target, *arguments):
        process = self.context.Process(target=target, args=(str(self.directory), *arguments))
        process.start()
        self.addCleanup(self.finish_worker, process)
        return process

    @staticmethod
    def finish_worker(process):
        process.join(timeout=1)
        if process.is_alive():
            process.terminate()
            process.join(timeout=3)

    def assert_finished(self, process):
        process.join(timeout=10)
        self.assertFalse(process.is_alive(), "Synthetic worker did not finish")
        self.assertEqual(process.exitcode, 0)

    def test_two_conditional_writers_have_one_winner(self):
        barrier = self.context.Barrier(2)
        outcomes = self.context.Queue()
        workers = [self.start_worker(_compete_write, self.key, barrier, outcomes) for _ in range(2)]
        for worker in workers:
            self.assert_finished(worker)
        self.assertCountEqual([outcomes.get(timeout=1), outcomes.get(timeout=1)], ["saved", "conflict"])
        self.assertEqual(self.store.read().credential.refresh_token, SYNTHETIC_TOKEN)
        outcomes.close()

    def test_old_operations_cannot_restore_after_clear_including_initial_absence(self):
        for initially_connected in [False, True]:
            with self.subTest(initially_connected=initially_connected):
                # First simulate initial absence, then an existing connection.
                if initially_connected:
                    self.store.replace(SenderCredential(SYNTHETIC_TOKEN, CLIENT_ID),
                                       expected_generation=self.store.read().generation)
                ready, proceed = self.context.Event(), self.context.Event()
                outcomes = self.context.Queue()
                worker = self.start_worker(_stale_write, self.key, ready, proceed, outcomes)
                self.assertTrue(ready.wait(timeout=8))
                cleared = self.store.clear(expected_generation=self.store.read().generation)
                proceed.set()
                self.assert_finished(worker)
                self.assertEqual(outcomes.get(timeout=1), "conflict")
                self.assertEqual(self.store.read(), cleared)
                outcomes.close()

    def test_separate_process_lock_contention_has_bounded_timeout(self):
        ready, release = self.context.Event(), self.context.Event()
        worker = self.start_worker(_hold_lock, ready, release)
        self.assertTrue(ready.wait(timeout=8))
        started = time.monotonic()
        try:
            with self.assertRaises(SenderStoreBusy):
                self.store.read()
            elapsed = time.monotonic() - started
            self.assertGreaterEqual(elapsed, 1.8)
            self.assertLess(elapsed, 5)
        finally:
            release.set()
        self.assert_finished(worker)
        self.assertIsNone(self.store.read().generation)
