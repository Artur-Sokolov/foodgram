from django.contrib.auth import get_user_model
from rest_framework import filters, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken

from .constants import (USERS_PAGINATION_PAGE_SIZE)
from .models import Subscription
from .serializers import (
    SignupSerializer, AdminUserSerializer, MeUserSerializer,
    ChangePasswordSerializer, AvatarSerializer, SubscriptionSerializer
)

User = get_user_model()


class CustomAuthToken(ObtainAuthToken):
    """Вход по email/паролю, возвращает токен."""
    pass


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Удаление токена текущего пользователя."""

    request.user.auth_token.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


class UsersPagination(PageNumberPagination):
    page_size = USERS_PAGINATION_PAGE_SIZE


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для пользователей: регистрация, профиль, подписки."""

    queryset = User.objects.all()
    lookup_field = 'id'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [AllowAny()]
        if self.action in [
            'me', 'set_password', 'avatar', 'subscribe', 'subscriptions'
        ]:
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        mapping = {
            'create': SignupSerializer,
            'me': MeUserSerializer,
            'set_password': ChangePasswordSerializer,
            'avatar': AvatarSerializer,
            'subscribe': SubscriptionSerializer,
            'subscriptions': SubscriptionSerializer,
        }
        return mapping.get(self.action, AdminUserSerializer)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output = AdminUserSerializer(user, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['POST'], url_path='set_password')
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(
            serializer.validated_data['current_password']
        ):
            return Response({'current_password': 'Неверный пароль'},
                            status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['put', 'delete'], url_path='avatar')
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = self.get_serializer(
                request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user
        if request.method == 'POST':
            if user == author:
                return Response({'detail': 'Нельзя подписаться на себя'},
                                status=status.HTTP_400_BAD_REQUEST)
            Subscription.objects.get_or_create(user=user, author=author)
            serializer = self.get_serializer(
                author, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        Subscription.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def subscriptions(self, request):
        subs = Subscription.objects.filter(
            user=request.user).values_list('author', flat=True)
        authors = User.objects.filter(id__in=subs)
        serializer = self.get_serializer(
            authors, many=True, context={'request': request})
        return Response(serializer.data)
