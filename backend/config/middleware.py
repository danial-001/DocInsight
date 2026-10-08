import uuid


class RequestIDMiddleware:
    """Generate a server-owned correlation ID; never trust a supplied header."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = str(uuid.uuid4())
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        if request.path.startswith("/api/v1/auth/"):
            response["Cache-Control"] = "no-store"
        return response
