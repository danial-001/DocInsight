from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, UserSerializer
from .services import login_account, logout_account
from .throttles import LoginThrottle


class CsrfView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrf_token": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = login_account(request._request, **serializer.validated_data)
        return Response({"user": UserSerializer(user).data, "csrf_token": get_token(request)})


class MeView(APIView):
    def get(self, request):
        return Response({"user": UserSerializer(request.user).data})


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    # Logging out remains possible when an existing account becomes suspended.
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        logout_account(request._request)
        return Response(status=204)
