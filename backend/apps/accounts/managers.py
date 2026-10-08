from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .validators import validate_password_length


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        """DocInsight policy: trim and lowercase the entire login address."""
        return super().normalize_email(email).strip().lower()

    def _create_user(self, email, password, **extra_fields):
        if not isinstance(email, str) or not email.strip():
            raise ValidationError({"email": "Email is required."})
        user = self.model(email=self.normalize_email(email), **extra_fields)
        # Validate fields/constraints before persisting; DB uniqueness handles races.
        user.full_clean(exclude=["password"])
        if password is not None:
            validate_password_length(password)
            validate_password(password, user=user)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        for flag in ("is_staff", "is_superuser"):
            if extra_fields.get(flag, False) is not False:
                raise ValueError("Ordinary user creation cannot grant privileged flags.")
            extra_fields[flag] = False
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        for flag in ("is_active", "is_staff", "is_superuser"):
            extra_fields.setdefault(flag, True)
            if extra_fields[flag] is not True:
                raise ValueError(f"Superuser must have {flag}=True.")
        if password is None:
            raise ValidationError({"password": "Superuser password is required."})
        # Explicitly trusted administrative provisioning; not public signup.
        if extra_fields.get("email_verified_at") is None:
            extra_fields["email_verified_at"] = timezone.now()
        return self._create_user(email, password, **extra_fields)
