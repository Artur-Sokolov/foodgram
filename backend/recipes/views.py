from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import HttpResponse

from .filters import RecipeFilter
from .pagination import RecipePagination
from .permissions import IsAuthorOrReadOnly
from .models import Recipe, Favorite, ShoppingCart
from .serializers import (RecipeCreateSerializer, RecipeReadSerializer,
                          DownloadShoppingCartSerializer,
)


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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """POST /recipes/{id}/favorite/"""

        recipe = self.get_object()
        Favorite.objects.get_or_create(user=request.user, recipe=recipe)
        return Response(status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def unfavorite(self, request, pk=None):
        """DELETE /recipes/{id}/favorite/"""

        recipe = self.get_object()
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """POST /recipes/{id}/shopping_cart/"""

        recipe = self.get_object()
        ShoppingCart.objects.get_or_create(user=request.user, recipe=recipe)
        return Response(status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """DELETE /recipes/{id}/shopping_cart/"""

        recipe = self.get_object()
        ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """GET /recipes/download_shopping_cart/ — скачивание списка покупок."""

        serializer = DownloadShoppingCartSerializer(request.user)
        data = serializer.data['ingredients']
        lines = [
            f"{item['name']} ({item['unit']}) — {item['amount']}"
            for item in data
        ]
        content = "\n".join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response
