from django.urls import include, path
from rest_framework.routers import DefaultRouter

from recipes.views import IngredientViewSet, RecipeViewSet, TagViewSet

from .views import CustomAuthToken, UserViewSet, logout_view

router_v1 = DefaultRouter()
router_v1.register(r'users', UserViewSet, basename='users')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register(r'tags', TagViewSet, basename='tags')
router_v1.register(r'ingredients', IngredientViewSet, basename='ingredients')

auth_urls = [
    path('auth/token/login/', CustomAuthToken.as_view(), name='login'),
    path('auth/token/logout/', logout_view, name='logout'),
]

urlpatterns = [
    path('', include(auth_urls)),
    path('', include(router_v1.urls)),
]