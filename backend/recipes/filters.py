from django_filters import rest_framework as filters
from django_filters.rest_framework import CharFilter, NumberFilter, BooleanFilter

from .models import Recipe


class RecipeFilter(filters.FilterSet):
    tags = CharFilter(method='filter_tags')
    author = NumberFilter(field_name='author__id')
    is_favorited = BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = BooleanFilter(method='filter_shopping_cart')

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        # getlist вернёт все ?tags=…&tags=…
        slugs = self.request.query_params.getlist('tags')
        if not slugs:
            return queryset
        return queryset.filter(tags__slug__in=slugs).distinct()

    def filter_favorited(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorited_by__user=user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(in_shopping_carts__user=user)
        return queryset
