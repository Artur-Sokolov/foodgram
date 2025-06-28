import base64, uuid
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from rest_framework import filters, viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .constants import (USERS_PAGINATION_PAGE_SIZE, USER_ME_URL_SEGMENT)
from .models import User, Subscription
from .permissions import IsAdmin
from .serializers import (
    SignupSerializer, AdminUserSerializer, MeUserSerializer,
    ChangePasswordSerializer, AvatarSerializer, SubscriptionSerializer,
    EmailAuthTokenSerializer
)


User = get_user_model()


class CustomAuthToken(ObtainAuthToken):
    """Вход по email/паролю, возвращает токен."""

    serializer_class = EmailAuthTokenSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key})


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
    serializer_class = AdminUserSerializer
    lookup_field = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    pagination_class = UsersPagination
    permission_classes = (IsAdmin,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    http_method_names = [
        'get', 'put', 'post', 'patch', 'delete', 'head', 'options'
    ]

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in [
            'me', 'set_password', 'avatar', 'subscribe', 'subscriptions'
        ]:
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['get', 'patch'],
        permission_classes=[IsAuthenticated],
        url_path=USER_ME_URL_SEGMENT,
        serializer_class=MeUserSerializer
    )
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)

        elif request.method == 'PATCH':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        elif request.method == 'PUT':
            serializer = AvatarSerializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

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

    @action(
        detail=False, methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def me_avatar(self, request):
        user = request.user

        # DELETE — удаляем аватар, отвечаем 204
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # PUT — пробуем получить avatar из request.data
        avatar_data = request.data.get('avatar')
        if not avatar_data:
            return Response(
                {'avatar': 'Поле avatar обязательно.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Если строка в формате base64
        if isinstance(avatar_data, str) and avatar_data.startswith('data:image'):
            header, b64 = avatar_data.split(';base64,', 1)
            ext = header.split('/')[-1]  # e.g. "png" или "jpeg"
            try:
                decoded = base64.b64decode(b64)
            except (TypeError, ValueError):
                return Response(
                    {'avatar': 'Некорректный base64.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            file_name = f'{uuid.uuid4()}.{ext}'
            user.avatar.save(file_name, ContentFile(decoded), save=True)

        # Иначе предполагаем, что это файл multipart/form-data
        else:
            avatar_file = request.FILES.get('avatar')
            if not avatar_file:
                return Response(
                    {'avatar': 'Неправильный формат avatar.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.avatar.save(avatar_file.name, avatar_file, save=True)

        # Отдаём новый URL аватара
        return Response({'avatar': request.build_absolute_uri(user.avatar.url)})
