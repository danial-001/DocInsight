from rest_framework.permissions import BasePermission


class CanManageEmailSender(BasePermission):
    """D-027 A: only active, verified, authenticated superusers may administer sender."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active
                    and user.is_email_verified and user.is_superuser)
