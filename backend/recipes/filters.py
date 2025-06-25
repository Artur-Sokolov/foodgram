from django_filters.rest_framework import (
    FilterSet, AllValuesMultipleFilter, NumberFilter, BooleanFilter
)

from .models import Recipe


class RecipeFilter(FilterSet):
    """
    Фильтр для модели Recipe.

    Параметры фильтрации:
      1. tags: фильтрация по slug тегов (можно несколько значений)
      2. author: фильтрация по ID автора
      3. is_favorited: булев флаг, если True —
      только избранные текущего пользователя
      4. is_in_shopping_cart: булев флаг, если True —
      только рецепты из списка покупок текущего пользователя
    """
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    author = NumberFilter(field_name='author__id')
    is_favorited = BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=user)
        return queryset
