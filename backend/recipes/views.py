import base64, uuid
from rest_framework.reverse import reverse
from django.core.files.base import ContentFile
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import HttpResponse

from .filters import RecipeFilter
from .pagination import RecipePagination
from .permissions import IsAuthorOrReadOnly
from .models import Recipe, Favorite, Ingredient, ShoppingCart, Tag
from .serializers import (RecipeCreateSerializer, RecipeReadSerializer,
                          DownloadShoppingCartSerializer, TagSerializer,
                          IngredientSerializer
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Список и просмотре тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'
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
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly
    ]
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
                return Response({'image': 'Некорректный base64.'},
                                status=status.HTTP_400_BAD_REQUEST)
            fname = f'{uuid.uuid4()}.{ext}'
            data['image'] = ContentFile(decoded, name=fname)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        read_serializer = RecipeReadSerializer(
            serializer.save(), context={'request': request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

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
                    status=status.HTTP_400_BAD_REQUEST
                )
            data['image'] = ContentFile(decoded, name=f'{uuid.uuid4()}.{ext}')

        serializer = RecipeCreateSerializer(
            instance, data=data, partial=partial, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save()

        read = RecipeReadSerializer(recipe, context={'request': request})
        return Response(read.data)

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

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
        permission_classes=[AllowAny]
    )
    def get_link(self, request, pk=None):
        url = reverse(
            'recipes-detail',
            kwargs={'pk': pk},
            request=request
        )
        return Response({'link': url})
