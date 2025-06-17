from django.conf import settings
from rest_framework import serializers

from .constants import (EMAIL_MAX_LENGTH, USER_MAX_LENGTH)
from .models import User
from .validators import validate_username


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        """Создание пользователя."""
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        return user


class TokenSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=USER_MAX_LENGTH,
        validators=[validate_username],
        required=True,
    )
    confirmation_code = serializers.CharField(
        max_length=settings.CONFIRMATION_CODE_LENGTH,
        min_length=settings.CONFIRMATION_CODE_LENGTH,
        required=True,
    )

class AdminUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role'
        )


class MeUserSerializer(AdminUserSerializer):

    class Meta(AdminUserSerializer.Meta):
        read_only_fields = ('role',)