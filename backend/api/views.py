from django.conf import settings
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from .constants import (USERS_PAGINATION_PAGE_SIZE)
from .models import User

from .permissions import IsAdmin
from .serializers import (AdminUserSerializer, MeUserSerializer)


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

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path=settings.USER_ME_URL_SEGMENT,
        permission_classes=[IsAuthenticated],
        serializer_class=MeUserSerializer
    )
    def profile(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
