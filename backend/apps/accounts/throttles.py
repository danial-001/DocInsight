from rest_framework.throttling import SimpleRateThrottle


class LoginThrottle(SimpleRateThrottle):
    scope = "login"

    def get_cache_key(self, request, view):
        # Deliberately ignore X-Forwarded-For; local proxy requests may share an IP.
        return self.cache_format % {"scope": self.scope, "ident": request.META.get("REMOTE_ADDR", "")}
