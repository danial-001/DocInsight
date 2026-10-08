from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone

from config.exceptions import InvalidCredentials


def login_account(request, *, email, password):
    user = authenticate(request, email=email, password=password)
    if user is None:
        raise InvalidCredentials()
    previous_key = request.session.session_key
    login(request, user)
    # Django retains the key when the same user logs in again; our contract rotates it.
    if previous_key is not None and request.session.session_key == previous_key:
        request.session.cycle_key()
    # Store an absolute deadline: later session writes cannot renew the eight hours.
    request.session.set_expiry(timezone.now() + timedelta(seconds=settings.SESSION_COOKIE_AGE))
    return user


def logout_account(request):
    logout(request)
