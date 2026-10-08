from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.http import Http404, JsonResponse
from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler


class InvalidCredentials(exceptions.APIException):
    status_code = 400
    default_detail = "Unable to log in with these credentials."
    default_code = "invalid_credentials"


def error_body(request, code, message, field_errors=None):
    return {"error": {
        "code": code,
        "message": message,
        "field_errors": field_errors if field_errors is not None else {},
        "request_id": request.request_id,
    }}


def csrf_failure(request, reason=""):
    # Framework diagnostics can include origin details; expose a stable safe message.
    return JsonResponse(error_body(request, "csrf_failed", "CSRF validation failed."), status=403)


def api_exception_handler(exc, context):
    request = context["request"]
    response = exception_handler(exc, context)
    if response is None:
        return Response(error_body(request, "internal_error", "An unexpected error occurred."), status=500)
    field_errors = {}
    if isinstance(exc, exceptions.ValidationError):
        code, message = "validation_error", "Please correct the supplied fields."
        field_errors = exc.detail if isinstance(exc.detail, dict) else {"non_field_errors": exc.detail}
    elif isinstance(exc, exceptions.NotAuthenticated):
        code, message = "authentication_required", "Please log in to continue."
    elif isinstance(exc, (exceptions.PermissionDenied, DjangoPermissionDenied)):
        code = "csrf_failed" if isinstance(exc, exceptions.PermissionDenied) and exc.get_codes() == "csrf_failed" else "permission_denied"
        message = "CSRF validation failed." if code == "csrf_failed" else "You do not have permission."
    elif isinstance(exc, Http404):
        code, message = "not_found", "The requested resource was not found."
    elif isinstance(exc, exceptions.Throttled):
        code, message = "rate_limited", "Too many requests. Please try again later."
    else:
        code = getattr(exc, "default_code", "request_failed")
        message = str(exc.default_detail)
    response.data = error_body(request, code, message, field_errors)
    return response
