from django.conf import settings

from django.db import models
from django.contrib.auth.models import AbstractUser
from .constants import (MAX_LENGTH_NAME, MAX_LENGTH_SLUG, USER_MAX_LENGTH,
                       EMAIL_MAX_LENGTH, MIN_SCORE, MAX_SCORE)
from .validators import validate_username


class User(AbstractUser):
    """Модель пользователя."""

    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'

    ROLE_CHOISES = [
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

    role = models.CharField(
        max_length=max(len(role_name) for role_name, _ in ROLE_CHOISES),
        choices=ROLE_CHOISES,
        default=USER,
        verbose_name='Роль',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
