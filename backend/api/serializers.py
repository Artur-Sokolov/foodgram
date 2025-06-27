from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import Subscription

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

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


class AdminUserSerializer(serializers.ModelSerializer):
    """Сериализатор для управления пользователями администратором."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'role', 'avatar'
        )


class MeUserSerializer(AdminUserSerializer):
    """Сериализатор для получения информации о текущем пользователе."""

    class Meta(AdminUserSerializer.Meta):
        read_only_fields = ('role', 'email', 'username')


class ChangePasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""

    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара пользователя."""

    class Meta:
        model = User
        fields = ('avatar',)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='author.recipes.count', read_only=True
    )


    class Meta:
        model = Subscription
        fields = ('id', 'user', 'author', 'is_subscribed', 'recipes_count')

    def get_is_subscribed(self, obj):
        """Проверка подписки пользователя на автора."""
        return True


class UsernameAuthTokenSerializer(serializers.Serializer):
    """Логин по username / password."""

    username = serializers.CharField(
        label=_('Username'),
        write_only=True,
    )
    password = serializers.CharField(
        label=_('Password'),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if not username or not password:
            raise serializers.ValidationError(
                _('Поля "username" и "password" обязательны.'),
                code='authorization'
            )

        user = authenticate(
            request=self.context.get('request'),
            username=username,
            password=password
        )
        if not user:
            raise serializers.ValidationError(
                _('Неверное имя пользователя или пароль.'),
                code='authorization'
            )

        attrs['user'] = user
        return attrs
