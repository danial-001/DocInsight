from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError


def validate_timezone(value):
    """Accept an installed IANA timezone name, never a filesystem path."""
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as error:
        raise ValidationError("Enter a valid IANA timezone name.", code="invalid_timezone") from error


def validate_password_length(password):
    if len(password) > 128:
        raise ValidationError("Password must be at most 128 characters.", code="password_too_long")
