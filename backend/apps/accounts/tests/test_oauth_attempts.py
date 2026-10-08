"""Synthetic database sessions/attempts only; no Google consent or token exchange."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import hashlib
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, connections, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client, TransactionTestCase, override_settings
from cryptography.fernet import Fernet
from django.utils import timezone

from apps.accounts.models import OAuthConnectionAttempt, User
from apps.accounts.oauth_pkce import code_challenge, InvalidOAuthPKCE, OAuthPKCEConfigurationError
from apps.accounts.oauth_attempts import (
    InvalidOAuthAttempt, OAuthAttemptInputError, OAuthAttemptTransactionError,
    claim_oauth_attempt, create_oauth_attempt,
)


BACKEND = "apps.accounts.authentication.VerifiedAccountBackend"
CLIENT_ID = "synthetic-oauth-client"


class AttemptFixture:
    def setUp(self):
        configured = override_settings(GMAIL_CREDENTIAL_ENCRYPTION_KEY=Fernet.generate_key().decode("ascii"))
        configured.enable()
        self.addCleanup(configured.disable)
        self.now = timezone.now().replace(microsecond=0)
        # Direct synthetic privileged fixtures, not real bootstrap/provisioning.
        self.user = User.objects.create(email="attempt-admin@example.com", password="!",
                                        is_superuser=True, email_verified_at=self.now)
        self.other = User.objects.create(email="other-admin@example.com", password="!",
                                         is_superuser=True, email_verified_at=self.now)
        self.key = self.session_for(self.user)
        self.other_key = self.session_for(self.other)

    def session_for(self, user):
        session = SessionStore()
        session.update({SESSION_KEY: str(user.pk), BACKEND_SESSION_KEY: BACKEND,
                        HASH_SESSION_KEY: user.get_session_auth_hash()})
        session.set_expiry(8 * 60 * 60)
        session.save()
        return session.session_key

    def issue(self, *, user=None, key=None, generation=None, at=None, client_id=CLIENT_ID):
        with patch("apps.accounts.oauth_attempts.timezone.now", return_value=at or self.now):
            return create_oauth_attempt((user or self.user).pk, key or self.key, client_id, generation)

    def claim(self, issued, *, user=None, key=None, at=None, client_id=CLIENT_ID):
        with patch("apps.accounts.oauth_attempts.timezone.now", return_value=at or self.now):
            return claim_oauth_attempt(issued.state, (user or self.user).pk, key or self.key, client_id)


class OAuthAttemptTests(AttemptFixture, TransactionTestCase):
    def test_hash_only_roundtrip_and_generation_context(self):
        generation = uuid4()
        issued = self.issue(generation=generation)
        record = OAuthConnectionAttempt.objects.get(pk=issued.id)
        self.assertRegex(issued.state, r"\A[0-9a-f]{64}\Z")
        self.assertEqual(record.state_digest, hashlib.sha256(issued.state.encode("ascii")).hexdigest())
        self.assertEqual(record.session_digest, hashlib.sha256(self.key.encode("ascii")).hexdigest())
        self.assertEqual(record.expires_at, self.now + timedelta(minutes=10))
        stored = repr(list(OAuthConnectionAttempt.objects.values()))
        self.assertNotIn(issued.state, stored)
        self.assertNotIn(self.key, stored)
        self.assertNotIn(issued.state, repr(issued))
        result = self.claim(issued)
        self.assertEqual(code_challenge(result.code_verifier), issued.code_challenge)
        self.assertEqual(issued.code_challenge_method, "S256")
        self.assertFalse(hasattr(issued, "code_verifier"))
        self.assertNotIn(result.code_verifier, stored)
        self.assertNotIn(result.code_verifier, repr(result))
        self.assertEqual((result.id, result.user_id, result.client_id, result.expected_generation),
                         (issued.id, self.user.pk, CLIENT_ID, generation))
        self.assertNotIn(issued.state, repr(result))
        self.assertNotIn(self.key, repr(result))
        record.refresh_from_db()
        self.assertEqual(record.claimed_at, self.now)
        self.assertIsNone(record.superseded_at)
        self.assertIsNone(record.encrypted_pkce_verifier)

    def test_initial_absence_generation_remains_none(self):
        self.assertIsNone(self.claim(self.issue()).expected_generation)

    def test_other_admins_pending_attempts_are_independent(self):
        first = self.issue()
        other = self.issue(user=self.other, key=self.other_key)
        self.claim(first)
        self.claim(other, user=self.other, key=self.other_key)

    def test_new_start_in_another_session_supersedes_old_pending(self):
        first = self.issue()
        second_key = self.session_for(self.user)
        second = self.issue(key=second_key, at=self.now + timedelta(seconds=1))
        with self.assertRaises(InvalidOAuthAttempt):
            self.claim(first, at=self.now + timedelta(seconds=2))
        old = OAuthConnectionAttempt.objects.get(pk=first.id)
        self.assertEqual(old.superseded_at, self.now + timedelta(seconds=1))
        self.assertIsNone(old.encrypted_pkce_verifier)
        self.claim(second, key=second_key, at=self.now + timedelta(seconds=2))

    def test_expired_unmarked_attempt_is_superseded_before_replacement(self):
        first = self.issue()
        second = self.issue(at=self.now + timedelta(minutes=11))
        self.assertIsNotNone(OAuthConnectionAttempt.objects.get(pk=first.id).superseded_at)
        self.claim(second, at=self.now + timedelta(minutes=11))

    def test_expiry_boundary_and_immediately_before_it(self):
        issued = self.issue()
        for at in [self.now + timedelta(minutes=10), self.now + timedelta(minutes=11)]:
            with self.subTest(at=at), self.assertRaises(InvalidOAuthAttempt):
                self.claim(issued, at=at)
        self.claim(issued, at=self.now + timedelta(minutes=10) - timedelta(microseconds=1))

    def test_replayed_and_unknown_states_share_safe_failure(self):
        issued = self.issue()
        self.claim(issued)
        messages = []
        for raw in [issued.state, None, "", {}, 123, "g" * 64, "A" * 64, "0" * 64, "a" * 10000]:
            with self.subTest(kind=type(raw).__name__), self.assertRaises(InvalidOAuthAttempt) as caught:
                claim_oauth_attempt(raw, self.user.pk, self.key, CLIENT_ID)
            messages.append((caught.exception.code, str(caught.exception)))
            self.assertNotIn(issued.state, str(caught.exception))
            self.assertNotIn(self.key, str(caught.exception))
        self.assertEqual(len(set(messages)), 1)

    def test_wrong_user_session_or_client_does_not_consume_valid_attempt(self):
        issued = self.issue()
        second_key = self.session_for(self.user)
        for fields in [{"user": self.other, "key": self.other_key}, {"key": second_key},
                       {"key": self.other_key}, {"client_id": "different-client"}]:
            with self.subTest(fields=tuple(fields)), self.assertRaises(InvalidOAuthAttempt):
                self.claim(issued, **fields)
        self.assertIsNone(OAuthConnectionAttempt.objects.get(pk=issued.id).claimed_at)
        self.claim(issued)

    def test_current_role_status_checked_at_creation_and_claim(self):
        issued = self.issue()
        for field, bad, good in [("is_superuser", False, True), ("is_active", False, True),
                                  ("email_verified_at", None, self.now)]:
            User.objects.filter(pk=self.user.pk).update(**{field: bad})
            with self.subTest(field=field):
                with self.assertRaises(InvalidOAuthAttempt):
                    self.issue()
                with self.assertRaises(InvalidOAuthAttempt):
                    self.claim(issued)
            User.objects.filter(pk=self.user.pk).update(**{field: good})
        record = OAuthConnectionAttempt.objects.get(pk=issued.id)
        self.assertIsNone(record.claimed_at)
        self.assertIsNone(record.superseded_at)
        self.claim(issued)

    def test_missing_and_expired_sessions_do_not_mutate_pending(self):
        issued = self.issue()
        Session.objects.filter(pk=self.key).update(expire_date=self.now)
        for action in [self.issue, lambda: self.claim(issued)]:
            with self.assertRaises(InvalidOAuthAttempt):
                action()
        Session.objects.filter(pk=self.key).delete()
        with self.assertRaises(InvalidOAuthAttempt):
            self.claim(issued)
        self.assertIsNone(OAuthConnectionAttempt.objects.get(pk=issued.id).superseded_at)

    def test_rotation_and_password_change_invalidate_binding(self):
        issued = self.issue()
        session = SessionStore(session_key=self.key)
        session.cycle_key()
        with self.assertRaises(InvalidOAuthAttempt):
            self.claim(issued)
        with self.assertRaises(InvalidOAuthAttempt):
            self.claim(issued, key=session.session_key)
        self.key = session.session_key
        replacement = self.issue()
        User.objects.filter(pk=self.user.pk).update(password="!synthetic-changed-password-hash")
        with self.assertRaises(InvalidOAuthAttempt):
            self.claim(replacement)

    def test_real_django_login_session_and_logout(self):
        self.user.set_password("Synthetic!Apricot-Mountain-482")
        self.user.save(update_fields=["password"])
        client = Client()
        self.assertTrue(client.login(email=self.user.email, password="Synthetic!Apricot-Mountain-482"))
        self.key = client.cookies[settings.SESSION_COOKIE_NAME].value
        issued = self.issue()
        client.logout()
        with self.assertRaises(InvalidOAuthAttempt):
            self.claim(issued)

    def test_signed_session_contents_must_match_live_user_and_backend(self):
        issued = self.issue()
        original = Session.objects.get(pk=self.key).session_data
        for data in [{}, [], {SESSION_KEY: str(self.other.pk), BACKEND_SESSION_KEY: BACKEND,
                             HASH_SESSION_KEY: self.user.get_session_auth_hash()},
                     {SESSION_KEY: str(self.user.pk), BACKEND_SESSION_KEY: "django.contrib.auth.backends.ModelBackend",
                      HASH_SESSION_KEY: self.user.get_session_auth_hash()},
                     {SESSION_KEY: str(self.user.pk), BACKEND_SESSION_KEY: BACKEND, HASH_SESSION_KEY: 123},
                     {SESSION_KEY: str(self.user.pk), BACKEND_SESSION_KEY: BACKEND, HASH_SESSION_KEY: "wrong"}]:
            Session.objects.filter(pk=self.key).update(session_data=SessionStore().encode(data))
            with self.subTest(kind=type(data).__name__), self.assertRaises(InvalidOAuthAttempt):
                self.claim(issued)
        Session.objects.filter(pk=self.key).update(session_data=original)
        self.claim(issued)

    def test_corrupt_session_is_safe_and_preserved(self):
        issued = self.issue()
        Session.objects.filter(pk=self.key).update(session_data="synthetic-corrupt-data")
        with self.assertLogs("django.security.SuspiciousSession", level="WARNING"), self.assertRaises(InvalidOAuthAttempt):
            self.claim(issued)
        self.assertEqual(Session.objects.get(pk=self.key).session_data, "synthetic-corrupt-data")

    def test_invalid_creation_input_does_not_supersede(self):
        issued = self.issue()
        valid = [self.user.pk, self.key, CLIENT_ID, None]
        for index, values in [(0, [None, "not-a-uuid", uuid4()]), (1, [None, {}, "", "x" * 10000]),
                              (2, [None, "", "x" * 513, "\ud800"]), (3, ["bad", 123, {}])]:
            for value in values:
                args = valid.copy()
                args[index] = value
                with self.subTest(index=index, kind=type(value).__name__), self.assertRaises(
                        (InvalidOAuthAttempt, OAuthAttemptInputError)):
                    create_oauth_attempt(*args)
        self.assertIsNone(OAuthConnectionAttempt.objects.get(pk=issued.id).superseded_at)

    def test_failed_insert_rolls_back_supersession(self):
        issued = self.issue()
        original = OAuthConnectionAttempt.objects.get(pk=issued.id).encrypted_pkce_verifier
        with patch("apps.accounts.oauth_attempts.OAuthConnectionAttempt.objects.create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.issue()
        self.assertIsNone(OAuthConnectionAttempt.objects.get(pk=issued.id).superseded_at)
        self.assertEqual(OAuthConnectionAttempt.objects.get(pk=issued.id).encrypted_pkce_verifier, original)
        self.claim(issued)

    def test_failed_claim_save_rolls_back_and_remains_usable(self):
        issued = self.issue()
        original = OAuthConnectionAttempt.objects.get(pk=issued.id).encrypted_pkce_verifier
        with patch.object(OAuthConnectionAttempt, "save", side_effect=RuntimeError("synthetic failure")):
            with self.assertRaises(RuntimeError):
                self.claim(issued)
        self.assertIsNone(OAuthConnectionAttempt.objects.get(pk=issued.id).claimed_at)
        self.assertEqual(OAuthConnectionAttempt.objects.get(pk=issued.id).encrypted_pkce_verifier, original)
        self.claim(issued)

    def test_nested_and_manual_transactions_rejected_without_changes(self):
        issued = self.issue()
        with transaction.atomic():
            for action in [self.issue, lambda: self.claim(issued)]:
                with self.assertRaises(OAuthAttemptTransactionError):
                    action()
        connection.set_autocommit(False)
        try:
            with self.assertRaises(OAuthAttemptTransactionError):
                self.claim(issued)
        finally:
            connection.rollback()
            connection.set_autocommit(True)
        self.assertIsNone(OAuthConnectionAttempt.objects.get(pk=issued.id).claimed_at)
        self.assertIsNone(OAuthConnectionAttempt.objects.get(pk=issued.id).superseded_at)

    def test_claim_commit_visible_independently_and_later_failure_cannot_undo(self):
        issued = self.issue()
        self.claim(issued)

        def inspect():
            close_old_connections()
            try:
                return OAuthConnectionAttempt.objects.get(pk=issued.id).claimed_at is not None
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=1) as executor:
            self.assertTrue(executor.submit(inspect).result(timeout=5))
        with self.assertRaises(RuntimeError), transaction.atomic():
            raise RuntimeError("synthetic later external failure; no provider called")
        with self.assertRaises(InvalidOAuthAttempt):
            self.claim(issued)
        next_attempt = self.issue()
        claimed = OAuthConnectionAttempt.objects.get(pk=issued.id)
        self.assertIsNotNone(claimed.claimed_at)
        self.assertIsNone(claimed.superseded_at)
        self.claim(next_attempt)

    def test_model_validation_digest_client_and_aware_times(self):
        record = OAuthConnectionAttempt.objects.get(pk=self.issue().id)
        record.full_clean()
        for field, value in [("state_digest", "A" * 64), ("session_digest", "z" * 64),
                             ("state_digest", "a" * 63), ("client_id", ""),
                             ("client_id", "a" * 513), ("client_id", "\ud800"),
                             ("created_at", self.now.replace(tzinfo=None)),
                             ("expires_at", "not-a-timestamp"), ("claimed_at", {}),
                             ("superseded_at", 123)]:
            original = getattr(record, field)
            setattr(record, field, value)
            with self.subTest(field=field), self.assertRaises(ValidationError):
                record.full_clean()
            setattr(record, field, original)

    def test_database_constraints_on_unique_pending_and_state_digest(self):
        issued = self.issue()
        record = OAuthConnectionAttempt.objects.get(pk=issued.id)
        for fields in [{}, {"created_at": self.now + timedelta(minutes=11),
                            "expires_at": self.now + timedelta(minutes=21)},
                       {"user": self.other, "state_digest": record.state_digest}]:
            values = dict(user=self.user, state_digest="f" * 64, session_digest="a" * 64,
                          encrypted_pkce_verifier="synthetic-shape-only",
                          client_id=CLIENT_ID, created_at=self.now, expires_at=self.now + timedelta(minutes=10))
            values.update(fields)
            with self.subTest(fields=tuple(fields)), self.assertRaises(IntegrityError), transaction.atomic():
                OAuthConnectionAttempt.objects.create(**values)

    def test_database_constraints_on_time_and_terminal_states(self):
        for fields in [{"expires_at": self.now}, {"expires_at": self.now - timedelta(seconds=1)},
                       {"claimed_at": self.now, "superseded_at": self.now},
                       {"claimed_at": self.now - timedelta(microseconds=1)},
                       {"claimed_at": self.now + timedelta(minutes=10)},
                       {"superseded_at": self.now - timedelta(microseconds=1)}]:
            values = dict(user=self.user, state_digest="f" * 64, session_digest="a" * 64,
                          encrypted_pkce_verifier="synthetic-shape-only",
                          client_id=CLIENT_ID, created_at=self.now, expires_at=self.now + timedelta(minutes=10))
            values.update(fields)
            if values.get("claimed_at") or values.get("superseded_at"):
                values["encrypted_pkce_verifier"] = None
            with self.subTest(fields=tuple(fields)), self.assertRaises(IntegrityError), transaction.atomic():
                OAuthConnectionAttempt.objects.create(**values)

    def test_retained_history_protects_user_without_verification_tokens(self):
        self.claim(self.issue())
        self.assertFalse(self.user.email_verification_tokens.exists())
        with self.assertRaises(ProtectedError):
            self.user.delete()
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_configuration_and_corruption_fail_without_consumption(self):
        issued = self.issue()
        record = OAuthConnectionAttempt.objects.get(pk=issued.id)
        original = record.encrypted_pkce_verifier
        for key in ["", "bad", Fernet.generate_key().decode("ascii")]:
            with override_settings(GMAIL_CREDENTIAL_ENCRYPTION_KEY=key):
                with self.assertRaises((InvalidOAuthPKCE, OAuthPKCEConfigurationError)):
                    self.claim(issued)
                if key in ("", "bad"):
                    with self.assertRaises(OAuthPKCEConfigurationError):
                        self.issue()
            record.refresh_from_db()
            self.assertIsNone(record.claimed_at)
            self.assertIsNone(record.superseded_at)
            self.assertEqual(record.encrypted_pkce_verifier, original)
        OAuthConnectionAttempt.objects.filter(pk=issued.id).update(encrypted_pkce_verifier="corrupt")
        with self.assertRaises(InvalidOAuthPKCE):
            self.claim(issued)
        OAuthConnectionAttempt.objects.filter(pk=issued.id).update(encrypted_pkce_verifier=original)
        self.claim(issued)

    def test_swapped_ciphertext_is_not_consumed(self):
        first = self.issue()
        second = self.issue(user=self.other, key=self.other_key)
        other_cipher = OAuthConnectionAttempt.objects.get(pk=second.id).encrypted_pkce_verifier
        OAuthConnectionAttempt.objects.filter(pk=first.id).update(encrypted_pkce_verifier=other_cipher)
        with self.assertRaises(InvalidOAuthPKCE):
            self.claim(first)
        self.assertIsNone(OAuthConnectionAttempt.objects.get(pk=first.id).claimed_at)
        self.claim(second, user=self.other, key=self.other_key)

    def test_database_shape_rejects_bypass_writes(self):
        issued = self.issue()
        for fields in [{"encrypted_pkce_verifier": None}, {"encrypted_pkce_verifier": ""},
                       {"claimed_at": self.now}, {"superseded_at": self.now}]:
            with self.subTest(fields=tuple(fields)), self.assertRaises(IntegrityError), transaction.atomic():
                OAuthConnectionAttempt.objects.filter(pk=issued.id).update(**fields)
        self.claim(issued)
        for value in ["", "synthetic"]:
            with self.assertRaises(IntegrityError), transaction.atomic():
                OAuthConnectionAttempt.objects.filter(pk=issued.id).update(encrypted_pkce_verifier=value)

    def test_invalid_context_is_rejected_before_decryption(self):
        issued = self.issue()
        with patch("apps.accounts.oauth_attempts.decrypt_verifier") as decrypt:
            with self.assertRaises(InvalidOAuthAttempt):
                self.claim(issued, client_id="wrong")
            with self.assertRaises(InvalidOAuthAttempt):
                self.claim(issued, at=self.now + timedelta(minutes=10))
            decrypt.assert_not_called()
        self.assertIsNotNone(OAuthConnectionAttempt.objects.get(pk=issued.id).encrypted_pkce_verifier)


class OAuthAttemptConcurrencyTests(AttemptFixture, TransactionTestCase):
    def competing(self, operations):
        self.assertEqual(connection.vendor, "postgresql")
        barrier = Barrier(len(operations))

        def run(operation):
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout = '5s'")
                    cursor.execute("SET lock_timeout = '4s'")
                    cursor.execute("SELECT pg_backend_pid()")
                    pid = cursor.fetchone()[0]
                barrier.wait(timeout=5)
                try:
                    result = operation()
                    return pid, "success", result
                except InvalidOAuthAttempt:
                    return pid, "invalid", None
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(operations)) as executor:
            futures = [executor.submit(run, operation) for operation in operations]
            results = [future.result(timeout=12) for future in futures]
        self.assertEqual(len({pid for pid, _, _ in results}), len(operations))
        return results

    def test_competing_callbacks_have_one_committed_claim(self):
        issued = create_oauth_attempt(self.user.pk, self.key, CLIENT_ID, None)
        operation = lambda: claim_oauth_attempt(issued.state, self.user.pk, self.key, CLIENT_ID)
        results = self.competing([operation, operation])
        self.assertEqual(sorted(outcome for _, outcome, _ in results), ["invalid", "success"])
        winners = [result for _, outcome, result in results if outcome == "success"]
        self.assertEqual(code_challenge(winners[0].code_verifier), issued.code_challenge)
        self.assertIsNone(OAuthConnectionAttempt.objects.get(pk=issued.id).encrypted_pkce_verifier)
        self.assertIsNotNone(OAuthConnectionAttempt.objects.get(pk=issued.id).claimed_at)

    def test_competing_first_starts_leave_one_pending(self):
        operation = lambda: create_oauth_attempt(self.user.pk, self.key, CLIENT_ID, None)
        results = self.competing([operation, operation])
        self.assertEqual([outcome for _, outcome, _ in results], ["success", "success"])
        pending = OAuthConnectionAttempt.objects.get(claimed_at=None, superseded_at=None)
        self.assertEqual(OAuthConnectionAttempt.objects.count(), 2)
        for _, _, issued in results:
            if issued.id != pending.pk:
                with self.assertRaises(InvalidOAuthAttempt):
                    claim_oauth_attempt(issued.state, self.user.pk, self.key, CLIENT_ID)

    def test_start_and_claim_race_has_consistent_terminal_state(self):
        issued = create_oauth_attempt(self.user.pk, self.key, CLIENT_ID, None)
        results = self.competing([
            lambda: claim_oauth_attempt(issued.state, self.user.pk, self.key, CLIENT_ID),
            lambda: create_oauth_attempt(self.user.pk, self.key, CLIENT_ID, None)])
        old = OAuthConnectionAttempt.objects.get(pk=issued.id)
        self.assertNotEqual(old.claimed_at is None, old.superseded_at is None)
        self.assertIsNone(old.encrypted_pkce_verifier)
        self.assertEqual(OAuthConnectionAttempt.objects.filter(claimed_at=None, superseded_at=None).count(), 1)
        outcomes = sorted(outcome for _, outcome, _ in results)
        self.assertEqual(outcomes, ["success", "success"] if old.claimed_at else ["invalid", "success"])

    def test_logout_racing_claim_either_commits_first_or_blocks_claim(self):
        issued = create_oauth_attempt(self.user.pk, self.key, CLIENT_ID, None)
        results = self.competing([
            lambda: claim_oauth_attempt(issued.state, self.user.pk, self.key, CLIENT_ID),
            lambda: Session.objects.filter(pk=self.key).delete()])
        record = OAuthConnectionAttempt.objects.get(pk=issued.id)
        outcomes = sorted(outcome for _, outcome, _ in results)
        self.assertEqual(outcomes, ["success", "success"] if record.claimed_at else ["invalid", "success"])
        self.assertFalse(Session.objects.filter(pk=self.key).exists())
