"""Internal token lifecycle. No HTTP, email delivery or account provisioning."""
import hashlib
import math
import re
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from .models import EmailVerificationToken, User


TOKEN_LIFETIME = timedelta(hours=1)
ISSUANCE_COOLDOWN = timedelta(seconds=60)
TOKEN_PATTERN = re.compile(r"\A[0-9a-f]{64}\Z")


class InvalidVerificationLink(Exception):
    code = "invalid_verification_link"

    def __init__(self):
        super().__init__("This verification link is invalid or no longer available.")


class VerificationCooldown(Exception):
    code = "verification_cooldown"

    def __init__(self, retry_after):
        self.retry_after = retry_after
        super().__init__("Please wait before requesting another verification link.")


def _token_digest(raw_token):
    return hashlib.sha256(raw_token.encode("ascii")).hexdigest()


@transaction.atomic
def issue_verification_token(user_id):
    """Return secret to trusted caller in memory, or None if already verified.

    Caller must wait for its outermost transaction to commit before delivery.
    Missing users raise User.DoesNotExist; this is not a public lookup endpoint.
    """
    user = User.objects.select_for_update().get(pk=user_id)
    if user.is_email_verified:
        return None
    now = timezone.now()  # Sample after any lock wait.
    latest = user.email_verification_tokens.order_by("-created_at", "-id").first()
    if latest is not None:
        remaining = latest.created_at + ISSUANCE_COOLDOWN - now
        if remaining > timedelta(0):
            raise VerificationCooldown(max(1, math.ceil(remaining.total_seconds())))
    raw_token = secrets.token_hex(32)
    user.email_verification_tokens.filter(consumed_at__isnull=True, revoked_at__isnull=True).update(revoked_at=now)
    EmailVerificationToken.objects.create(user=user, token_digest=_token_digest(raw_token),
                                          created_at=now, expires_at=now + TOKEN_LIFETIME)
    return raw_token


@transaction.atomic
def consume_verification_token(raw_token):
    """Verify only the token's user once; never unsuspend or create a session."""
    if not isinstance(raw_token, str) or TOKEN_PATTERN.fullmatch(raw_token) is None:
        raise InvalidVerificationLink()
    digest = _token_digest(raw_token)
    # Discover owner without taking a token lock; every mutating path locks User first.
    user_id = EmailVerificationToken.objects.filter(token_digest=digest).values_list("user_id", flat=True).first()
    if user_id is None:
        raise InvalidVerificationLink()
    try:
        user = User.objects.select_for_update().get(pk=user_id)
        token = EmailVerificationToken.objects.select_for_update().get(token_digest=digest, user_id=user_id)
    except (User.DoesNotExist, EmailVerificationToken.DoesNotExist):
        raise InvalidVerificationLink() from None
    now = timezone.now()
    if user.is_email_verified or token.consumed_at is not None or token.revoked_at is not None or now >= token.expires_at:
        raise InvalidVerificationLink()
    token.consumed_at = now
    token.save(update_fields=["consumed_at"])
    user.email_verified_at = now
    user.save(update_fields=["email_verified_at"])
    return user
