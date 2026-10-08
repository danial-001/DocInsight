from django.contrib.auth.backends import ModelBackend
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied


class VerifiedAccountBackend(ModelBackend):
    """Enforce independent active/verified gates on credentials and session lookup."""

    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and user.is_email_verified


class AccountSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        try:
            super().enforce_csrf(request)
        except PermissionDenied:
            raise PermissionDenied("CSRF validation failed.", code="csrf_failed") from None
