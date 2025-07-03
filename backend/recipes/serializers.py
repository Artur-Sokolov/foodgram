from django.contrib.auth import get_user_model
from django.db.models import Sum
from rest_framework import serializers

from api.serializers import UserReadSerializer

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

User = get_user_model()


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
    """Сериалайзер для ингредиента внутри рецепта"""

    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all(), write_only=True
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
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and (
            obj.favorited_by.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and (
            obj.in_shopping_carts.filter(user=user).exists()
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True,
    )
    ingredients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            required=True,
        ),
        required=True,
    )
    image = serializers.ImageField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text',
            'cooking_time', 'tags', 'ingredients', 'image'
        )

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым'
            )
        ingredient = [item.get('id') for item in ingredients]
        if len(ingredient) != len(set(ingredient)):
            raise serializers.ValidationError(
                'Ингредиенты не должны дублироваться'
            )
        return ingredients

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            **validated_data, author=self.context['request'].user
        )
        recipe.tags.set(tags)
        for ing in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe, ingredient_id=ing['id'], amount=ing['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            tags = validated_data.pop('tags')
            instance.tags.set(tags)

        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            RecipeIngredient.objects.filter(recipe=instance).delete()
            for ingredients in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredients['id'],
                    amount=ingredients['amount'],
                )
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
        qs = (
            RecipeIngredient.objects.filter(
                recipe__in=obj.shopping_cart.values_list('recipe', flat=True)
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(amount=Sum('amount'))
        )
        return [
            {
                'name': item['ingredient__name'],
                'unit': item['ingredient__measurement_unit'],
                'amount': item['amount'],
            }
            for item in qs
        ]


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    """Мини-сериализатор рецепта для списка в выдаче подписок."""

    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
