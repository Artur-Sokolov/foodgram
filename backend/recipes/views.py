from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets, permissions

from .filters import RecipeFilter
from .pagination import RecipePagination
from .permissions import IsAuthorOrReadOnly
from .models import Recipe
from .serializers import RecipeCreateSerializer, RecipeReadSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related('tags', 'ingredients')
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly
    ]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filter_class = RecipeFilter

    pagination_class = RecipePagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
