import uuid
import time
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404
from django.test import TestCase, override_settings
from django.urls import include, path
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.urls import urlpatterns as account_patterns


class ForbiddenView(APIView):
    def get(self, request):
        raise PermissionDenied()


class MutationView(APIView):
    def post(self, request):
        return Response({"ok": True})


class FailureView(APIView):
    def get(self, request, kind):
        failures = {"missing": Http404, "forbidden": DjangoPermissionDenied, "unexpected": RuntimeError}
        raise failures[kind]("sensitive diagnostic must not be returned")


# Test-only routes exercise shared handling; these are not production endpoints.
urlpatterns = [path("api/v1/auth/", include(account_patterns)),
               path("forbidden", ForbiddenView.as_view()), path("mutation", MutationView.as_view()),
               path("api/v1/auth/test-failure/<str:kind>", FailureView.as_view())]


class AuthAPITests(TestCase):
    password = "Quartz!River9-Orbit7"
    prefix = "/api/v1/auth/"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("first@example.com", cls.password,
                                           email_verified_at=timezone.now())
        cls.other = User.objects.create_user("second@example.com", cls.password,
                                            email_verified_at=timezone.now())
        cls.pending = User.objects.create_user("pending@example.com", cls.password)
        cls.suspended = User.objects.create_user("suspended@example.com", cls.password,
                                                email_verified_at=timezone.now(), is_active=False)
        cls.unusable = User.objects.create_user("unusable@example.com", email_verified_at=timezone.now())

    def setUp(self):
        cache.clear()
        self.client = APIClient(enforce_csrf_checks=True)

    def csrf(self, client=None):
        return (client or self.client).get(self.prefix + "csrf").json()["csrf_token"]

    def login(self, client=None, email=None, password=None):
        client = client or self.client
        return client.post(self.prefix + "login", {
            "email": email or self.user.email,
            "password": password if password is not None else self.password,
        }, format="json", HTTP_X_CSRFTOKEN=self.csrf(client))

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status, response.content)
        body = response.json()["error"]
        self.assertEqual(set(body), {"code", "message", "field_errors", "request_id"})
        self.assertEqual(body["code"], code)
        self.assertEqual(str(uuid.UUID(body["request_id"])), response["X-Request-ID"])
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn(self.password, response.content.decode())
        return body

    def test_csrf_and_anonymous_contract(self):
        response = self.client.get(self.prefix + "csrf", HTTP_X_REQUEST_ID="untrusted")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertIn(settings.CSRF_COOKIE_NAME, response.cookies)
        self.assertNotEqual(response["X-Request-ID"], "untrusted")
        self.assert_error(self.client.get(self.prefix + "me"), 403, "authentication_required")

    def test_login_me_cookie_contract_and_canonical_email(self):
        response = self.login(email=" FIRST@EXAMPLE.COM ")
        self.assertEqual(response.status_code, 200, response.content)
        user = response.json()["user"]
        self.assertEqual(set(user), {"id", "email", "first_name", "last_name", "timezone"})
        self.assertEqual(user["id"], str(self.user.id))
        self.assertEqual(self.client.get(self.prefix + "me").json(), {"user": user})
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["domain"], "")
        self.assertEqual(bool(cookie["secure"]), settings.SESSION_COOKIE_SECURE)
        self.assertLessEqual(int(cookie["max-age"]), 28800)
        self.assertGreaterEqual(int(cookie["max-age"]), 28798)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("password", response.content.decode())

    @override_settings(SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)
    def test_secure_cookie_settings(self):
        response = self.login()
        self.assertTrue(response.cookies[settings.SESSION_COOKIE_NAME]["secure"])
        self.assertTrue(response.cookies[settings.CSRF_COOKIE_NAME]["secure"])

    def test_invalid_accounts_have_identical_safe_response(self):
        bodies = []
        for email, password in [("missing@example.com", self.password),
                                (self.user.email, "wrong"), (self.pending.email, self.password),
                                (self.suspended.email, self.password), (self.unusable.email, self.password)]:
            body = self.assert_error(self.login(email=email, password=password), 400, "invalid_credentials")
            bodies.append({k: v for k, v in body.items() if k != "request_id"})
            self.assertNotIn(settings.SESSION_COOKIE_NAME, self.client.cookies)
        self.assertTrue(all(body == bodies[0] for body in bodies))

    def test_validation_and_overlong_password_rejected_before_authentication(self):
        token = self.csrf()
        with patch("apps.accounts.services.authenticate") as authenticate:
            for data in [{}, {"email": "bad", "password": "valid"},
                         {"email": self.user.email, "password": "x" * 129},
                         {"email": self.user.email, "password": 123456789012}]:
                response = self.client.post(self.prefix + "login", data, format="json", HTTP_X_CSRFTOKEN=token)
                self.assert_error(response, 400, "validation_error")
            authenticate.assert_not_called()

    def test_login_and_logout_require_csrf_even_anonymous(self):
        for endpoint in ["login", "logout"]:
            self.assert_error(self.client.post(self.prefix + endpoint, {}, format="json"), 403, "csrf_failed")
            self.csrf()
            self.assert_error(self.client.post(self.prefix + endpoint, {}, format="json",
                                               HTTP_X_CSRFTOKEN="bad"), 403, "csrf_failed")
        self.assert_error(self.client.post(self.prefix + "login", {}, format="json",
                                           HTTP_X_CSRFTOKEN=self.csrf(), HTTP_ORIGIN="https://hostile.example"),
                          403, "csrf_failed")

    def test_login_rotates_session_and_csrf(self):
        old_token = self.csrf()
        session = self.client.session
        session["prelogin_marker"] = True
        session.save()
        old_key = session.session_key
        response = self.client.post(self.prefix + "login", {"email": self.user.email, "password": self.password},
                                    format="json", HTTP_X_CSRFTOKEN=old_token)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.client.session.session_key, old_key)
        self.assertFalse(Session.objects.filter(session_key=old_key).exists())
        first_login_key = self.client.session.session_key
        first_login_token = response.json()["csrf_token"]
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(self.client.session.session_key, first_login_key)
        self.assertFalse(Session.objects.filter(session_key=first_login_key).exists())
        self.assert_error(self.client.post(self.prefix + "logout", HTTP_X_CSRFTOKEN=first_login_token), 403, "csrf_failed")
        self.assert_error(self.client.post(self.prefix + "logout", HTTP_X_CSRFTOKEN=old_token), 403, "csrf_failed")
        self.assertEqual(self.client.post(self.prefix + "logout",
                                         HTTP_X_CSRFTOKEN=response.json()["csrf_token"]).status_code, 204)

    def test_fixed_expiry_does_not_renew_and_expired_session_is_denied(self):
        self.login()
        session = self.client.session
        record = Session.objects.get(session_key=session.session_key)
        deadline = record.expire_date
        self.assertAlmostEqual((deadline - timezone.now()).total_seconds(), 28800, delta=3)
        with patch("django.utils.timezone.now", return_value=timezone.now() + timedelta(hours=1)):
            response = self.client.get(self.prefix + "me")
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)
            changed = self.client.session
            changed["test_write"] = True
            changed.save()
        record.refresh_from_db()
        self.assertEqual(record.expire_date, deadline)
        Session.objects.filter(pk=record.pk).update(expire_date=timezone.now() - timedelta(seconds=1))
        self.assert_error(self.client.get(self.prefix + "me"), 403, "authentication_required")

    def test_existing_session_denied_after_suspension_or_verification_removed(self):
        for field, value in [("is_active", False), ("email_verified_at", None)]:
            with self.subTest(field=field):
                User.objects.filter(pk=self.user.pk).update(is_active=True, email_verified_at=timezone.now())
                self.assertEqual(self.login().status_code, 200)
                User.objects.filter(pk=self.user.pk).update(**{field: value})
                self.assert_error(self.client.get(self.prefix + "me"), 403, "authentication_required")
                self.assertEqual(self.client.post(self.prefix + "logout", HTTP_X_CSRFTOKEN=self.csrf()).status_code, 204)

    def test_two_clients_are_separate_and_logout_invalidates_old_cookie(self):
        other_client = APIClient(enforce_csrf_checks=True)
        self.login()
        self.login(client=other_client, email=self.other.email)
        old_cookie = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertEqual(self.client.get(self.prefix + "me").json()["user"]["id"], str(self.user.id))
        self.assertEqual(other_client.get(self.prefix + "me").json()["user"]["id"], str(self.other.id))
        response = self.client.post(self.prefix + "logout", HTTP_X_CSRFTOKEN=self.csrf())
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(Session.objects.filter(session_key=old_cookie).exists())
        replay = APIClient(enforce_csrf_checks=True)
        replay.cookies[settings.SESSION_COOKIE_NAME] = old_cookie
        self.assert_error(replay.get(self.prefix + "me"), 403, "authentication_required")
        self.assertEqual(self.client.post(self.prefix + "logout", HTTP_X_CSRFTOKEN=self.csrf()).status_code, 204)
        self.assertEqual(other_client.get(self.prefix + "me").status_code, 200)

    def test_login_throttle_ignores_forwarded_ip_and_recovers(self):
        token = self.csrf()
        for index in range(10):
            response = self.client.post(self.prefix + "login", {}, format="json", HTTP_X_CSRFTOKEN=token,
                                        HTTP_X_FORWARDED_FOR=f"192.0.2.{index}")
            self.assertEqual(response.status_code, 400)
        response = self.client.post(self.prefix + "login", {}, format="json", HTTP_X_CSRFTOKEN=token)
        self.assert_error(response, 429, "rate_limited")
        self.assertGreater(int(response["Retry-After"]), 0)
        self.assertEqual(self.client.post(self.prefix + "login", {}, format="json", HTTP_X_CSRFTOKEN=token,
                                          REMOTE_ADDR="192.0.2.200").status_code, 400)
        with patch("apps.accounts.throttles.LoginThrottle.timer", return_value=time.time() + 61):
            self.assertEqual(self.client.post(self.prefix + "login", {}, format="json",
                                              HTTP_X_CSRFTOKEN=token).status_code, 400)

    @override_settings(ROOT_URLCONF=__name__)
    def test_permission_and_authenticated_csrf_errors_have_distinct_codes(self):
        self.login()
        response = self.client.get("/forbidden")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "permission_denied")
        response = self.client.post("/mutation", {}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "csrf_failed")
        self.assertEqual(self.client.post("/mutation", {}, format="json",
                                          HTTP_X_CSRFTOKEN=self.csrf()).status_code, 200)

    def test_malformed_json_and_wrong_method_are_safe(self):
        response = self.client.post(self.prefix + "login", "{", content_type="application/json",
                                    HTTP_X_CSRFTOKEN=self.csrf())
        self.assert_error(response, 400, "parse_error")
        self.assert_error(self.client.get(self.prefix + "login"), 405, "method_not_allowed")

    @override_settings(ROOT_URLCONF=__name__)
    def test_framework_and_unexpected_errors_are_safe(self):
        self.login()
        for kind, status, code in [("missing", 404, "not_found"), ("forbidden", 403, "permission_denied"),
                                   ("unexpected", 500, "internal_error")]:
            response = self.client.get(self.prefix + "test-failure/" + kind)
            self.assert_error(response, status, code)
            self.assertNotIn("sensitive diagnostic", response.content.decode())
