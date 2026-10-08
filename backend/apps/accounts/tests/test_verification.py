import hashlib
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, connections, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from apps.accounts.models import EmailVerificationToken, User
from apps.accounts.verification import (
    InvalidVerificationLink, VerificationCooldown, consume_verification_token, issue_verification_token,
)


class VerificationTests(TestCase):
    def setUp(self):
        # Explicit synthetic account fixtures; no email delivery or registration.
        self.user = User.objects.create_user("verification@example.com")
        self.other = User.objects.create_user("other@example.com")
        self.now = timezone.now()

    def issue(self, at=None, user=None):
        with patch("apps.accounts.verification.timezone.now", return_value=at or self.now):
            return issue_verification_token((user or self.user).pk)

    def consume(self, raw_token, at=None):
        with patch("apps.accounts.verification.timezone.now", return_value=at or self.now):
            return consume_verification_token(raw_token)

    def test_issuance_stores_only_digest_uuid_and_one_hour_lifetime(self):
        raw = self.issue()
        self.assertTrue(isinstance(raw, str) and re.fullmatch(r"[0-9a-f]{64}", raw) is not None)
        record = EmailVerificationToken.objects.get(user=self.user)
        self.assertIsInstance(record.pk, uuid.UUID)
        self.assertEqual(record.token_digest, hashlib.sha256(raw.encode("ascii")).hexdigest())
        self.assertTrue(all(str(value) != raw for value in record.__dict__.values()))
        self.assertEqual(record.created_at, self.now)
        self.assertEqual(record.expires_at, self.now + timedelta(hours=1))
        self.assertTrue(timezone.is_aware(record.expires_at))
        self.assertIsNone(record.consumed_at)
        self.assertIsNone(record.revoked_at)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.email_verified_at)

    def test_cooldown_and_exact_boundary_preserve_history(self):
        old_raw = self.issue()
        old = EmailVerificationToken.objects.get(user=self.user)
        for elapsed, wait in [(0, 60), (59, 1), (59.5, 1)]:
            with self.subTest(elapsed=elapsed), self.assertRaises(VerificationCooldown) as caught:
                self.issue(self.now + timedelta(seconds=elapsed))
            self.assertEqual(caught.exception.retry_after, wait)
        old.refresh_from_db()
        self.assertIsNone(old.revoked_at)
        new_raw = self.issue(self.now + timedelta(seconds=60))
        old.refresh_from_db()
        self.assertEqual(old.revoked_at, self.now + timedelta(seconds=60))
        self.assertIsNone(old.consumed_at)
        self.assertEqual(EmailVerificationToken.objects.filter(user=self.user).count(), 2)
        with self.assertRaises(InvalidVerificationLink):
            self.consume(old_raw, self.now + timedelta(seconds=61))
        self.consume(new_raw, self.now + timedelta(seconds=61))

    def test_single_use_verifies_only_own_user_without_session(self):
        raw = self.issue()
        self.issue(user=self.other)
        verified = self.consume(raw, self.now + timedelta(seconds=1))
        self.assertEqual(verified.pk, self.user.pk)
        self.user.refresh_from_db()
        self.other.refresh_from_db()
        self.assertEqual(self.user.email_verified_at, self.now + timedelta(seconds=1))
        self.assertIsNone(self.other.email_verified_at)
        with self.assertRaises(InvalidVerificationLink):
            self.consume(raw, self.now + timedelta(seconds=2))
        from django.contrib.sessions.models import Session
        self.assertEqual(Session.objects.count(), 0)

    def test_expiry_boundary_and_replacement_of_expired_outstanding_row(self):
        raw = self.issue()
        for elapsed in [3600, 3601]:
            with self.subTest(elapsed=elapsed), self.assertRaises(InvalidVerificationLink):
                self.consume(raw, self.now + timedelta(seconds=elapsed))
        self.user.refresh_from_db()
        record = EmailVerificationToken.objects.get(user=self.user)
        self.assertIsNone(self.user.email_verified_at)
        self.assertIsNone(record.consumed_at)
        self.assertIsNone(record.revoked_at)
        replacement = self.issue(self.now + timedelta(hours=2))
        record.refresh_from_db()
        self.assertIsNotNone(record.revoked_at)
        self.consume(replacement, self.now + timedelta(hours=2, seconds=1))

    def test_immediately_before_expiry_is_valid(self):
        self.consume(self.issue(), self.now + timedelta(hours=1) - timedelta(microseconds=1))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_invalid_and_unknown_links_share_safe_error_and_no_changes(self):
        self.issue()
        before = list(EmailVerificationToken.objects.values())
        messages = []
        for raw in [None, 123, {}, "", "bad", "g" * 64, "A" * 64, "0" * 64, "x" * 10000]:
            with self.subTest(kind=type(raw).__name__), self.assertRaises(InvalidVerificationLink) as caught:
                self.consume(raw)
            messages.append((str(caught.exception), caught.exception.code))
        self.assertEqual(len(set(messages)), 1)
        self.assertEqual(list(EmailVerificationToken.objects.values()), before)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)

    def test_verified_user_is_not_reissued_or_consumed_again(self):
        raw = self.issue()
        User.objects.filter(pk=self.user.pk).update(email_verified_at=self.now)
        before = list(EmailVerificationToken.objects.values())
        self.assertIsNone(self.issue())
        with self.assertRaises(InvalidVerificationLink):
            self.consume(raw)
        self.assertEqual(list(EmailVerificationToken.objects.values()), before)

    def test_verification_preserves_suspension(self):
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        self.consume(self.issue())
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertFalse(self.user.is_active)

    def test_failed_replacement_rolls_back_old_revocation(self):
        old_raw = self.issue()
        with patch("apps.accounts.verification.EmailVerificationToken.objects.create", side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                self.issue(self.now + timedelta(minutes=2))
        old = EmailVerificationToken.objects.get(user=self.user)
        self.assertIsNone(old.revoked_at)
        self.consume(old_raw, self.now + timedelta(minutes=2))

    def test_failed_user_save_rolls_back_consumption(self):
        raw = self.issue()
        with patch.object(User, "save", side_effect=RuntimeError("synthetic write failure")):
            with self.assertRaises(RuntimeError):
                self.consume(raw)
        self.assertIsNone(EmailVerificationToken.objects.get(user=self.user).consumed_at)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_email_verified)
        self.consume(raw)

    def test_outer_transaction_rollback_removes_issuance(self):
        with self.assertRaises(RuntimeError), transaction.atomic():
            self.issue()
            raise RuntimeError("synthetic rollback")
        self.assertFalse(EmailVerificationToken.objects.exists())

    def test_digest_format_validation(self):
        record = EmailVerificationToken(user=self.user, token_digest="a" * 64,
                                        created_at=self.now, expires_at=self.now + timedelta(hours=1))
        record.full_clean()
        for digest in ["A" * 64, "z" * 64, "a" * 63, "a" * 64 + "\n"]:
            record.token_digest = digest
            with self.subTest(length=len(digest)), self.assertRaises(ValidationError):
                record.full_clean()

    def test_database_rejects_duplicate_digest_even_across_users(self):
        self.issue()
        record = EmailVerificationToken.objects.get(user=self.user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            EmailVerificationToken.objects.create(user=self.other, token_digest=record.token_digest,
                                                  created_at=self.now, expires_at=self.now + timedelta(hours=1))

    def test_database_outstanding_constraint_includes_expired_rows(self):
        self.issue()
        for created in [self.now, self.now + timedelta(hours=2)]:
            with self.subTest(created=created), self.assertRaises(IntegrityError), transaction.atomic():
                EmailVerificationToken.objects.create(user=self.user, token_digest="f" * 64,
                                                      created_at=created, expires_at=created + timedelta(hours=1))

    def test_database_rejects_invalid_expiry_and_conflicting_states(self):
        for fields in [{"expires_at": self.now}, {"expires_at": self.now - timedelta(seconds=1)},
                       {"consumed_at": self.now, "revoked_at": self.now}]:
            values = {"user": self.user, "token_digest": "a" * 64, "created_at": self.now,
                      "expires_at": self.now + timedelta(hours=1)}
            values.update(fields)
            with self.subTest(fields=tuple(fields)), self.assertRaises(IntegrityError), transaction.atomic():
                EmailVerificationToken.objects.create(**values)

    def test_user_deletion_is_protected_for_retained_history(self):
        self.consume(self.issue())
        with self.assertRaises(ProtectedError):
            self.user.delete()
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())
        self.assertEqual(EmailVerificationToken.objects.count(), 1)


class VerificationConcurrencyTests(TransactionTestCase):
    """Independent PostgreSQL connections; no TestCase transaction hiding locks."""

    def setUp(self):
        self.user = User.objects.create_user("concurrent@example.com")

    def run_competing(self, operations):
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
                    outcome = "no_issue" if result is None else "success"
                except (VerificationCooldown, InvalidVerificationLink) as exc:
                    outcome = exc.code
                return pid, outcome
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(operations)) as executor:
            futures = [executor.submit(run, operation) for operation in operations]
            results = [future.result(timeout=12) for future in futures]
        self.assertEqual(len({pid for pid, _ in results}), len(operations))
        return sorted(outcome for _, outcome in results)

    def test_competing_first_issuances_create_one_outstanding_record(self):
        issue = lambda: issue_verification_token(self.user.pk)
        self.assertEqual(self.run_competing([issue, issue]), ["success", "verification_cooldown"])
        self.assertEqual(EmailVerificationToken.objects.filter(user=self.user).count(), 1)

    def test_competing_resends_revoke_once_and_issue_once(self):
        with patch("apps.accounts.verification.timezone.now", return_value=timezone.now() - timedelta(minutes=2)):
            old_raw = issue_verification_token(self.user.pk)
        issue = lambda: issue_verification_token(self.user.pk)
        self.assertEqual(self.run_competing([issue, issue]), ["success", "verification_cooldown"])
        self.assertEqual(EmailVerificationToken.objects.filter(user=self.user).count(), 2)
        self.assertEqual(EmailVerificationToken.objects.filter(user=self.user, consumed_at=None, revoked_at=None).count(), 1)
        with self.assertRaises(InvalidVerificationLink):
            consume_verification_token(old_raw)

    def test_competing_confirmations_have_one_success(self):
        raw = issue_verification_token(self.user.pk)
        consume = lambda: consume_verification_token(raw)
        self.assertEqual(self.run_competing([consume, consume]), ["invalid_verification_link", "success"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
        self.assertIsNotNone(EmailVerificationToken.objects.get(user=self.user).consumed_at)

    def test_resend_and_confirmation_race_has_consistent_final_state(self):
        with patch("apps.accounts.verification.timezone.now", return_value=timezone.now() - timedelta(minutes=2)):
            raw = issue_verification_token(self.user.pk)
        outcomes = self.run_competing([lambda: issue_verification_token(self.user.pk),
                                       lambda: consume_verification_token(raw)])
        self.user.refresh_from_db()
        if self.user.is_email_verified:
            self.assertEqual(outcomes, ["no_issue", "success"])
            self.assertEqual(EmailVerificationToken.objects.filter(user=self.user).count(), 1)
            self.assertEqual(EmailVerificationToken.objects.filter(user=self.user, consumed_at=None, revoked_at=None).count(), 0)
        else:
            self.assertEqual(outcomes, ["invalid_verification_link", "success"])
            self.assertEqual(EmailVerificationToken.objects.filter(user=self.user).count(), 2)
            self.assertEqual(EmailVerificationToken.objects.filter(user=self.user, consumed_at=None, revoked_at=None).count(), 1)
