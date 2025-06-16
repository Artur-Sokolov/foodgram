# from django.conf import settings
from rest_framework import serializers

from .models import User


class AdminUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role'
        )


class MeUserSerializer(AdminUserSerializer):

    class Meta(AdminUserSerializer.Meta):
        read_only_fields = ('role',)