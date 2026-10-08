from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import include, path
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.permissions import CanManageEmailSender
from apps.accounts.urls import urlpatterns as account_patterns


class SenderPermissionProbe(APIView):
    # Test-only view: this is not a Gmail endpoint or provider simulation.
    permission_classes = [CanManageEmailSender]

    def get(self, request):
        return Response({"allowed": True})

    def post(self, request):
        return Response(status=204)


urlpatterns = [path("api/v1/auth/", include(account_patterns)),
               path("permission-probe", SenderPermissionProbe.as_view())]


@override_settings(ROOT_URLCONF=__name__)
class SenderPermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Unusable fixture passwords: force_login sets real sessions without credential shortcuts in production.
        cls.ordinary = User.objects.create_user("ordinary@example.com", email_verified_at=timezone.now())
        cls.staff = User.objects.create_user("staff@example.com", email_verified_at=timezone.now())
        cls.staff.is_staff = True
        cls.staff.save(update_fields=["is_staff"])
        cls.admin = User.objects.create_user("admin@example.com", email_verified_at=timezone.now())
        cls.second_admin = User.objects.create_user("admin2@example.com", email_verified_at=timezone.now())
        cls.pending = User.objects.create_user("pending-admin@example.com")
        cls.suspended = User.objects.create_user("suspended-admin@example.com", email_verified_at=timezone.now(),
                                                is_active=False)
        for user in [cls.admin, cls.second_admin, cls.pending, cls.suspended]:
            user.is_superuser = True
            user.save(update_fields=["is_superuser"])

    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf(self):
        return self.client.get("/api/v1/auth/csrf").json()["csrf_token"]

    def test_permission_contract_independently_rejects_ineligible_identities(self):
        guard = CanManageEmailSender()
        for user, allowed in [(AnonymousUser(), False), (self.ordinary, False), (self.staff, False),
                              (self.pending, False), (self.suspended, False),
                              (self.admin, True), (self.second_admin, True)]:
            with self.subTest(identity=str(user.pk)):
                self.assertEqual(guard.has_permission(SimpleNamespace(user=user), None), allowed)

    def test_session_role_matrix_and_standard_error_codes(self):
        response = self.client.get("/permission-probe")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")
        for user, code in [(self.ordinary, "permission_denied"), (self.staff, "permission_denied"),
                           (self.pending, "authentication_required"), (self.suspended, "authentication_required"),
                           (self.admin, None), (self.second_admin, None)]:
            with self.subTest(identity=str(user.pk)):
                self.client.force_login(user)
                response = self.client.get("/permission-probe")
                self.assertEqual(response.status_code, 200 if code is None else 403)
                if code:
                    self.assertEqual(response.json()["error"]["code"], code)
                    self.assertEqual(response.json()["error"]["request_id"], response["X-Request-ID"])
                self.client.logout()

    def test_approved_admin_mutation_requires_csrf(self):
        self.client.force_login(self.admin)
        response = self.client.post("/permission-probe", {}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "csrf_failed")
        self.assertEqual(self.client.post("/permission-probe", {}, format="json",
                                          HTTP_X_CSRFTOKEN=self.csrf()).status_code, 204)

    def test_csrf_does_not_grant_ordinary_or_staff_sender_access(self):
        for user in [self.ordinary, self.staff]:
            with self.subTest(identity=str(user.pk)):
                self.client.force_login(user)
                response = self.client.post("/permission-probe", {}, format="json", HTTP_X_CSRFTOKEN=self.csrf())
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["error"]["code"], "permission_denied")
                self.client.logout()

    def test_existing_session_loses_access_on_next_request_after_revocation(self):
        for field, value, code in [("is_superuser", False, "permission_denied"),
                                   ("is_active", False, "authentication_required"),
                                   ("email_verified_at", None, "authentication_required")]:
            with self.subTest(field=field):
                User.objects.filter(pk=self.admin.pk).update(is_superuser=True, is_active=True,
                                                             email_verified_at=timezone.now())
                self.client.force_login(self.admin)
                self.assertEqual(self.client.get("/permission-probe").status_code, 200)
                User.objects.filter(pk=self.admin.pk).update(**{field: value})
                response = self.client.get("/permission-probe")
                self.assertEqual(response.status_code, 403)
                self.assertEqual(response.json()["error"]["code"], code)
