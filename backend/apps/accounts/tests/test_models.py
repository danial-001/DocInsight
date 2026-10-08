import uuid

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import User


class UserModelTests(TestCase):
    password = "Quartz!River9-Orbit7"

    def test_normalized_identity_defaults_and_password_hash(self):
        user = User.objects.create_user("  Sample@EXAMPLE.COM  ", self.password)
        user.refresh_from_db()
        self.assertIsInstance(user.id, uuid.UUID)
        self.assertEqual(user.email, "sample@example.com")
        self.assertEqual(user.timezone, "UTC")
        self.assertTrue(timezone.is_aware(user.date_joined))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_email_verified)
        self.assertEqual((user.first_name, user.last_name), ("", ""))
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(user.check_password(self.password))
        self.assertFalse(user.check_password("wrong"))

    def test_missing_password_is_unusable(self):
        user = User.objects.create_user("unusable@example.com")
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.check_password(""))

    def test_duplicate_email_rejected_by_manager(self):
        User.objects.create_user("sample@example.com", self.password)
        with self.assertRaises(ValidationError):
            User.objects.create_user("SAMPLE@EXAMPLE.COM", self.password)

    def test_case_duplicate_rejected_even_when_save_validation_bypassed(self):
        User.objects.create_user("sample@example.com", self.password)
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(email="SAMPLE@EXAMPLE.COM", password="!")])
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_email_or_timezone_never_persisted(self):
        for email, zone in [("", "UTC"), ("not-an-email", "UTC"),
                            ("zone@example.com", "Not/AZone"),
                            ("zone@example.com", "../UTC")]:
            with self.subTest(email=email, zone=zone), self.assertRaises(ValidationError):
                User.objects.create_user(email, self.password, timezone=zone)
        self.assertEqual(User.objects.count(), 0)

    def test_valid_timezone(self):
        user = User.objects.create_user("zone@example.com", self.password, timezone="Asia/Karachi")
        self.assertEqual(user.timezone, "Asia/Karachi")

    def test_password_policy_rejects_invalid_passwords_without_writes(self):
        for password in ["short", "123456789012345", "password",
                         "p" * 129, "similar@example.com"]:
            with self.subTest(password_length=len(password)), self.assertRaises(ValidationError):
                User.objects.create_user("similar@example.com", password)
        self.assertEqual(User.objects.count(), 0)

    def test_long_password_rejected_before_hashing(self):
        from unittest.mock import patch
        with patch.object(User, "set_password") as set_password:
            with self.assertRaises(ValidationError):
                User.objects.create_user("long@example.com", "p" * 129)
            set_password.assert_not_called()

    def test_ordinary_creation_cannot_grant_privileges(self):
        for flag in ["is_staff", "is_superuser"]:
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                User.objects.create_user("ordinary@example.com", self.password, **{flag: True})
        self.assertEqual(User.objects.count(), 0)

    def test_superuser_is_explicitly_trusted(self):
        user = User.objects.create_superuser("ADMIN@example.com", self.password)
        self.assertTrue(user.is_active and user.is_staff and user.is_superuser)
        self.assertTrue(user.is_email_verified)
        self.assertTrue(timezone.is_aware(user.email_verified_at))
        self.assertTrue(user.check_password(self.password))

    def test_superuser_rejects_false_flags_and_missing_password(self):
        for flag in ["is_active", "is_staff", "is_superuser"]:
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                User.objects.create_superuser("admin@example.com", self.password, **{flag: False})
        with self.assertRaises(ValidationError):
            User.objects.create_superuser("admin@example.com")
        self.assertEqual(User.objects.count(), 0)

    def test_verification_does_not_reactivate_suspended_account(self):
        user = User.objects.create_user("suspended@example.com", self.password, is_active=False)
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at"])
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.is_active)

    def test_suspension_does_not_erase_verification(self):
        user = User.objects.create_user("verified@example.com", self.password,
                                        email_verified_at=timezone.now())
        user.is_active = False
        user.save(update_fields=["is_active"])
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.is_active)
