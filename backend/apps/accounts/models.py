import uuid
from datetime import datetime

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.conf import settings
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone as django_timezone

from .managers import UserManager
from .validators import validate_timezone


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150, blank=True, default="")
    last_name = models.CharField(max_length=150, blank=True, default="")
    timezone = models.CharField(max_length=64, default="UTC", validators=[validate_timezone])
    date_joined = models.DateTimeField(default=django_timezone.now)
    email_verified_at = models.DateTimeField(null=True, blank=True, default=None)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_unique")]

    @property
    def is_email_verified(self):
        return self.email_verified_at is not None

    def clean(self):        
        super().clean()
        self.email = UserManager.normalize_email(self.email)

    def save(self, *args, **kwargs):
        self.email = UserManager.normalize_email(self.email)
        return super().save(*args, **kwargs)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def __str__(self):
        return self.email


class EmailVerificationToken(models.Model):
    """Issuance history only: the original secret is never persisted."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                             related_name="email_verification_tokens")
    token_digest = models.CharField(max_length=64, unique=True, validators=[
        RegexValidator(r"\A[0-9a-f]{64}\Z", "Digest must be 64 lowercase hexadecimal characters.")
    ])
    created_at = models.DateTimeField(default=django_timezone.now)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True, default=None)
    revoked_at = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(expires_at__gt=models.F("created_at")),
                                   name="accounts_token_expiry_after_creation"),
            models.CheckConstraint(condition=models.Q(consumed_at__isnull=True) | models.Q(revoked_at__isnull=True),
                                   name="accounts_token_not_used_and_revoked"),
            models.UniqueConstraint(fields=["user"],
                                    condition=models.Q(consumed_at__isnull=True, revoked_at__isnull=True),
                                    name="accounts_token_one_outstanding"),
        ]
        indexes = [models.Index(fields=["user", "created_at"], name="accounts_token_user_created")]


class OAuthConnectionAttempt(models.Model):
    """Retained connection proof metadata; not Google credentials or delivery state."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                             related_name="oauth_connection_attempts")
    state_digest = models.CharField(max_length=64, unique=True, validators=[
        RegexValidator(r"\A[0-9a-f]{64}\Z", "Digest must be 64 lowercase hexadecimal characters.")])
    session_digest = models.CharField(max_length=64, validators=[
        RegexValidator(r"\A[0-9a-f]{64}\Z", "Digest must be 64 lowercase hexadecimal characters.")])
    client_id = models.CharField(max_length=512)
    expected_generation = models.UUIDField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(default=django_timezone.now)
    expires_at = models.DateTimeField()
    claimed_at = models.DateTimeField(null=True, blank=True, default=None)
    superseded_at = models.DateTimeField(null=True, blank=True, default=None)
    encrypted_pkce_verifier = models.CharField(max_length=1024, null=True, blank=True,
                                              default=None, editable=False)

    def clean_fields(self, exclude=None):
        # Django's DateTimeField conversion can raise TypeError for e.g. integers
        # before clean() runs. Turn those types into ordinary validation failures.
        for name in ("created_at", "expires_at", "claimed_at", "superseded_at"):
            if name not in (exclude or ()):
                value = getattr(self, name)
                if value is not None and not isinstance(value, (datetime, str)):
                    raise ValidationError({name: "An aware timestamp is required."})
        super().clean_fields(exclude=exclude)

    def clean(self):
        super().clean()
        for name in ("created_at", "expires_at", "claimed_at", "superseded_at"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, datetime) or django_timezone.is_naive(value)):
                raise ValidationError({name: "An aware timestamp is required."})
        try:
            self.client_id.encode("utf-8")
        except (AttributeError, UnicodeError):
            raise ValidationError({"client_id": "A valid client ID is required."}) from None

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user"],
                                    condition=models.Q(claimed_at__isnull=True, superseded_at__isnull=True),
                                    name="accounts_oauth_one_pending"),
            models.CheckConstraint(condition=(
                models.Q(claimed_at__isnull=True, superseded_at__isnull=True,
                         encrypted_pkce_verifier__isnull=False) & ~models.Q(encrypted_pkce_verifier="")
            ) | (
                (models.Q(claimed_at__isnull=False) | models.Q(superseded_at__isnull=False))
                & models.Q(encrypted_pkce_verifier__isnull=True)
            ), name="accounts_oauth_pkce_shape"),
            models.CheckConstraint(condition=models.Q(expires_at__gt=models.F("created_at")),
                                   name="accounts_oauth_expiry_after"),
            models.CheckConstraint(condition=models.Q(claimed_at__isnull=True) | models.Q(superseded_at__isnull=True),
                                   name="accounts_oauth_one_terminal"),
            models.CheckConstraint(condition=models.Q(claimed_at__isnull=True) | (
                models.Q(claimed_at__gte=models.F("created_at")) & models.Q(claimed_at__lt=models.F("expires_at"))),
                name="accounts_oauth_claim_in_window"),
            models.CheckConstraint(condition=models.Q(superseded_at__isnull=True) | models.Q(
                superseded_at__gte=models.F("created_at")), name="accounts_oauth_superseded_after"),
        ]
        indexes = [models.Index(fields=["user", "created_at"], name="accounts_oauth_user_created")]
