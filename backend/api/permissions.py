from django.contrib.auth import get_user_model
from rest_framework import permissions

User = get_user_model()


class IsAdmin(permissions.BasePermission):
    """
    Доступ только для админа.
    Для неавторизованных вернёт 401,
    для авторизованных, но не-админов — 403.
    """

    def has_permission(self, request, view):
        user = request.user
        return (user.is_authenticated and user.is_admin)


class IsAdminOrModerator(IsAdmin):
    """Доступ для админа и модератора."""

    def has_permission(self, request, view):
        return super().has_permission(request, view) or (
            request.user.is_authenticated and request.user.is_moderator
        )


class IsAdminOrReadOnly(IsAdmin):
    message = 'Создавать и изменять записи может только администратор.'

    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or super().has_permission(request, view)
        )
