from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import EMAIL_MAX_LENGTH, USER_MAX_LENGTH
from .validators import validate_username


class User(AbstractUser):
    """Модель пользователя."""

    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'

    ROLE_CHOIСES = [
        (USER, 'Пользователь'),
        (MODERATOR, 'Модератор'),
        (ADMIN, 'Администратор'),
    ]

    username = models.CharField(
        max_length=USER_MAX_LENGTH,
        unique=True,
        validators=[validate_username],
        verbose_name='Никнейм'
    )

    email = models.EmailField(
        unique=True,
        max_length=EMAIL_MAX_LENGTH,
        verbose_name='Электронная почта',
    )

    first_name = models.CharField(
        max_length=USER_MAX_LENGTH,
        verbose_name='Имя',
    )

    last_name = models.CharField(
        max_length=USER_MAX_LENGTH,
        verbose_name='Фамилия',
    )

    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True,
        verbose_name='Аватар пользователя',
    )

    role = models.CharField(
        max_length=max(len(role_name) for role_name, _ in ROLE_CHOIСES),
        choices=ROLE_CHOIСES,
        default=USER,
        verbose_name='Роль',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель подписки пользователя на автора."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followering'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'author')
