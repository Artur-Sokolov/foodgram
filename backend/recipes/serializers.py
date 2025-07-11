from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework import serializers

from api.serializers import UserReadSerializer
from api.constants import (
    MIN_COOKING_TIME, MAX_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT, MAX_INGREDIENT_AMOUNT
)
from .models import (
    Favorite, Ingredient, Recipe,
    RecipeIngredient, ShoppingCart, Tag
)

User = get_user_model()


class IngredientCreateSerializer(serializers.Serializer):
    """ Сериализатор для отдельного ингредиента."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )

    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        max_value=MAX_INGREDIENT_AMOUNT,
    )


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для ингредиента внутри рецепта."""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all(),
        write_only=True
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    author = UserReadSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return bool(
            user.is_authenticated
            and obj.favorited_by.filter(user=user).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return bool(
            user.is_authenticated
            and obj.in_shopping_carts.filter(user=user).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True
    )
    ingredients = IngredientCreateSerializer(many=True, required=True)

    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
    )
    image = serializers.ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text',
            'cooking_time', 'tags', 'ingredients',
            'image'
        )

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым')
        ids = [item['id'] for item in ingredients]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны дублироваться')
        return ingredients

    def _create_ingredients(self, recipe, ingredients_data):
        objs = [
            RecipeIngredient(
                recipe=recipe,
                ingredient_id=(
                    item['id'].id if hasattr(item['id'], 'id')
                    else item['id']),
                amount=item['amount']
            )
            for item in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(objs)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            author=self.context['request'].user, **validated_data)
        recipe.tags.set(tags)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            instance.tags.set(validated_data.pop('tags'))
        if 'ingredients' in validated_data:
            instance.recipe_ingredients.all().delete()
            self._create_ingredients(
                instance, validated_data.pop('ingredients'))
        return super().update(instance, validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    """Добавление/удаление из избранного."""

    class Meta:
        model = Favorite
        fields = ('recipe',)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Добавление/удаление в список покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)


class DownloadShoppingCartSerializer(serializers.Serializer):
    """Сериализатор для скачивания списка покупок."""

    ingredients = serializers.SerializerMethodField()

    def get_ingredients(self, obj):
        queryset = (
            RecipeIngredient.objects
            .filter(
                recipe__in=obj.shopping_cart.values_list('recipe', flat=True))
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
        )
        return [
            {'name': item['ingredient__name'],
             'unit': item['ingredient__measurement_unit'],
             'amount': item['amount']}
            for item in queryset
        ]


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Мини-сериализатор рецепта для списка подписок."""

    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
