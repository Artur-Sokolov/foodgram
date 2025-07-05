import base64
import uuid

from django.core.files.base import ContentFile
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .filters import RecipeFilter
from .models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from .pagination import RecipePagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (DownloadShoppingCartSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeMinifiedSerializer,
                          RecipeReadSerializer, TagSerializer)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Список и просмотре тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Спислк и просмотр рецептов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['^name']
    search_param = 'name'
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().prefetch_related('tags', 'ingredients')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = RecipeFilter

    pagination_class = RecipePagination

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeReadSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        image = data.get('image')

        if isinstance(image, str) and image.startswith('data:image'):
            header, b64 = image.split(';base64', 1)
            ext = header.split('/')[-1]
            try:
                decoded = base64.b64decode(b64)
            except (TypeError, ValueError):
                return Response(
                    {'image': 'Некорректный base64.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            fname = f'{uuid.uuid4()}.{ext}'
            data['image'] = ContentFile(decoded, name=fname)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        read_serializer = RecipeReadSerializer(
            serializer.save(), context={'request': request}
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        params = request.query_params

        if 'is_in_shopping_cart' in params:
            return super().list(request, *args, **kwargs)

        if 'is_favorited' in params or 'author' in params:
            return super().list(request, *args, **kwargs)

        tags = params.getlist('tags')
        if not tags:
            return Response(
                {'count': 0, 'next': None, 'previous': None, 'results': []}
            )
        return super().list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()

        image = data.get('image')
        if isinstance(image, str) and image.startswith('data:image'):
            header, b64 = image.split(';base64,', 1)
            ext = header.split('/')[-1]
            try:
                decoded = base64.b64decode(b64)
            except (TypeError, ValueError):
                return Response(
                    {'image': 'Некорректный base64.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            data['image'] = ContentFile(decoded, name=f'{uuid.uuid4()}.{ext}')

        serializer = RecipeCreateSerializer(
            instance, data=data, partial=partial, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        read = RecipeReadSerializer(recipe, context={'request': request})
        return Response(read.data)

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """POST добавить рецепт в избранное."""
        recipe = self.get_object()
        favorite, created = Favorite.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            return Response(
                {'detail': 'Рецепт уже в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = RecipeMinifiedSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def unfavorite(self, request, pk=None):
        """DELETE удалить рецепт из избранного."""

        recipe = self.get_object()
        deleted, _ = request.user.favorites.filter(recipe=recipe).delete()
        if deleted == 0:
            return Response(
                {'detail': 'Рецепта нет в избранном'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=['post'], permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """POST добавить рецепт в список покупок."""

        recipe = self.get_object()
        cart_item, created = ShoppingCart.objects.get_or_create(
            user=request.user, recipe=recipe
        )
        if not created:
            return Response(
                {'detail': 'Рецепт уже в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RecipeMinifiedSerializer(
            recipe, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """DELETE рецепт из списка покупок."""

        recipe = self.get_object()
        deleted, _ = request.user.shopping_cart.filter(recipe=recipe).delete()
        if deleted == 0:
            return Response(
                {'detail': 'Рецепта нет в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=['get'], permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """GET /recipes/download_shopping_cart/ — скачивание списка покупок."""

        serializer = DownloadShoppingCartSerializer(request.user)
        data = serializer.data['ingredients']
        lines = [
            f"({item['name']} ({item['unit']}) — {item['amount']})"
            for item in data
        ]
        content = '\n'.join(lines)
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"')
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        url = reverse('recipes-detail', kwargs={'pk': pk}, request=request)
        return Response({'short-link': url})
