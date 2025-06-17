from django.conf import settings
from django.db import IntegrityError
from rest_framework import filters, viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


from .constants import (USERS_PAGINATION_PAGE_SIZE)
from .models import User

from .permissions import IsAdmin
from .serializers import (AdminUserSerializer, SignupSerializer,)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout user с удалением токена."""
    try:
        request.user.auth_token.delete()
    except (AttributeError, Token.DoesNotExist):
        pass
    return Response(status=status.HTTP_204_NO_CONTENT)


class UsersPagination(PageNumberPagination):
    page_size = USERS_PAGINATION_PAGE_SIZE


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    lookup_field = 'username'
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']
    pagination_class = UsersPagination
    permission_classes = (IsAdmin,)
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return SignupSerializer
        return AdminUserSerializer
