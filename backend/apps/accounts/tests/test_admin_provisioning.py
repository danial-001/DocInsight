import os
from io import StringIO
from unittest.mock import Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.accounts.models import User


class AdminProvisioningTests(TestCase):
    # Public synthetic fixture, never a real administrator credential.
    password = "Quartz!River9-Orbit7"

    def setUp(self):
        self.stdout = StringIO()
        self.stderr = StringIO()

    def command(self, email, interactive=False, **options):
        call_command("createsuperuser", email=email, interactive=interactive,
                     stdout=self.stdout, stderr=self.stderr, **options)

    def test_interactive_command_creates_trusted_normalized_hashed_admin(self):
        stdin = Mock()
        stdin.isatty.return_value = True
        with patch("django.contrib.auth.management.commands.createsuperuser.getpass.getpass",
                   side_effect=[self.password, self.password]):
            self.command("OWNER@EXAMPLE.COM", interactive=True, stdin=stdin)
        user = User.objects.get(email="owner@example.com")
        self.assertTrue(user.is_active and user.is_staff and user.is_superuser and user.is_email_verified)
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)
        self.assertNotIn(self.password, self.stdout.getvalue() + self.stderr.getvalue())

    def test_interactive_password_validation_bypass_cannot_override_manager_policy(self):
        stdin = Mock()
        stdin.isatty.return_value = True
        with patch("django.contrib.auth.management.commands.createsuperuser.getpass.getpass", return_value="short"), \
                patch("builtins.input", return_value="y"):
            with self.assertRaises(CommandError):
                self.command("owner@example.com", interactive=True, stdin=stdin)
        self.assertEqual(User.objects.count(), 0)

    def test_noninteractive_weak_or_overlong_password_is_rejected(self):
        for password in ["short", "123456789012345", "x" * 129]:
            with self.subTest(length=len(password)), patch.dict(os.environ, {"DJANGO_SUPERUSER_PASSWORD": password}):
                with self.assertRaises(CommandError):
                    self.command("owner@example.com")
        self.assertEqual(User.objects.count(), 0)

    def test_missing_password_never_creates_unusable_privileged_account(self):
        with patch.dict(os.environ):
            os.environ.pop("DJANGO_SUPERUSER_PASSWORD", None)
            with self.assertRaises(CommandError):
                self.command("owner@example.com")
        self.assertEqual(User.objects.count(), 0)

    def test_duplicate_existing_user_is_not_promoted_or_reset(self):
        existing = User.objects.create_user("owner@example.com", self.password)
        before = (existing.pk, existing.password, existing.email_verified_at, existing.is_staff, existing.is_superuser)
        for email in ["owner@example.com", "OWNER@EXAMPLE.COM"]:
            with self.subTest(email=email), patch.dict(os.environ, {"DJANGO_SUPERUSER_PASSWORD": self.password}):
                with self.assertRaises(CommandError):
                    self.command(email)
        existing.refresh_from_db()
        self.assertEqual((existing.pk, existing.password, existing.email_verified_at,
                          existing.is_staff, existing.is_superuser), before)
        self.assertEqual(User.objects.count(), 1)

    def test_interactive_non_tty_skips_without_provisioning(self):
        stdin = Mock()
        stdin.isatty.return_value = False
        self.command("owner@example.com", interactive=True, stdin=stdin)
        self.assertEqual(User.objects.count(), 0)
        self.assertIn("not running in a TTY", self.stdout.getvalue())
