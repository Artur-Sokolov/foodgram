from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Subscription

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'password',
            'first_name', 'last_name'
        )

    def create(self, validated_data):
        """Создание пользователя."""
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        return user


class AdminUserSerializer(serializers.ModelSerializer):
    """Сериализатор для управления пользователями администратором."""

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name',
            'last_name', 'role', 'avatar'
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


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для списка моих подписок с рецептами."""

    email = serializers.EmailField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    avatar = serializers.ImageField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, author):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return author.followering.filter(user=user).exists()

    def get_recipes(self, author):
        from recipes.serializers import RecipeMinifiedSerializer

        request = self.context['request']
        limit = request.query_params.get('recipes_limit')
        recipe = author.recipes.all().order_by('-pub_date')
        try:
            limit = int(limit) if limit is not None else None
        except ValueError:
            limit = None
        if limit:
            recipe = recipe[:limit]
        return RecipeMinifiedSerializer(recipe,
                                        many=True, context=self.context).data


class EmailAuthTokenSerializer(serializers.Serializer):
    """Логин по email/password."""

    email = serializers.EmailField(
        label=_('Email'),
        write_only=True,
    )
    password = serializers.CharField(
        label=_('Password'),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise serializers.ValidationError(
                _('Поля "email" и "password" обязательны.'),
                code='authorization'
            )

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            raise serializers.ValidationError(
                _('Неверный e-mail или пароль.'), code='authorization'
            )

        attrs['user'] = user
        return attrs


class UserReadSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        """True, если текущий аутентифицированный user подписан на obj."""

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return user.follower.filter(author=obj).exists()
