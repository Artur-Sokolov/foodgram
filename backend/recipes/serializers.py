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



