from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag)

from .models import Subscription, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Кастомный админ для модели User."""

    list_display = (
        'id', 'username', 'email', 'last_name', 'first_name', 'role'
    )
    list_filter = ('role',)
    search_fields = ('email', 'username')
    ordering = ('id',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name')}),
        (
            'Права доступа',
            {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')},
        ),
        ('Дополнительно', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username', 'first_name', 'last_name',
                    'email', 'password1', 'password2'
                ),
            },
        ),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для модели Tag."""

    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для модели Ingredient."""

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    autocomplete_fields = ['ingredient']
    verbose_name = 'Ингредиент в рецепте'
    verbose_name_plural = 'Ингредиенты в рецепте'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для модели Recipe."""

    inlines = (RecipeIngredientInline,)

    filter_horizontal = ('tags',)
    list_display = (
        'id',
        'name',
        'author',
        'cooking_time',
        'pub_date',
        'favorites_count',
    )
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'tags')
    ordering = ('-pub_date',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(_favorites_count=Count('favorited_by'))

    def favorites_count(self, obj):
        """Количество добавлений в избранное."""

        return obj._favorites_count

    favorites_count.short_description = 'Добавлено в избранное'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для модели Favorite."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для модели ShoppingCart."""

    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Админка для модели Subscription ."""

    list_display = ('id', 'user', 'author')
    search_fields = ('user__username', 'author__username')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Recipe Ingraadient."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
