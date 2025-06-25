from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Tag, Ingredient, Recipe, RecipeIngredient

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
        source='ingredient',
        queryset=Ingredient.objects.all(),
        write_only=True
    )
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов с вложенными полями."""

    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True, read_only=True
    )
    author = serializers.StringRelatedField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'name', 'image', 'text',
            'cooking_time', 'tags', 'ingredients', 'pub_date'
        )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True
    )
    ingredients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
        )
    )
    image = serializers.ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'text', 'cooking_time',
            'tags', 'ingredients', 'image'
        )

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым'
            )
        ids = [item.get('id') for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны дублироваться'
            )
        return value

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(
            **validated_data, author=self.context['request'].user)
        recipe.tags.set(tags)
        for ing in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ing['id'],
                amount=ing['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        instance.tags.set(validated_data.pop('tags'))
        ingredients_data = validated_data.pop('ingredients')
        RecipeIngredient.objects.filter(recipe=instance).delete()
        for ing in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient_id=ing['id'],
                amount=ing['amount']
            )
        return super().update(instance, validated_data)
