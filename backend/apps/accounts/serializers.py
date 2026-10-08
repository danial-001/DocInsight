from rest_framework import serializers

from .managers import UserManager
from .models import User


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)

    def validate_email(self, value):
        return UserManager.normalize_email(value)

    def validate_password(self, value):
        if not isinstance(self.initial_data.get("password"), str):
            raise serializers.ValidationError("Password must be a string.")
        return value


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "timezone")
        read_only_fields = fields
