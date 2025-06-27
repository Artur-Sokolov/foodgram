from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CustomAuthToken, logout_view, UserViewSet)
from recipes.views import (RecipeViewSet)


router_v1 = DefaultRouter()
router_v1.register(r'users', UserViewSet, basename='users')
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')

auth_urls = [
    path('auth/token/login/', CustomAuthToken.as_view(), name='login'),
    path('auth/token/logout/', logout_view, name='logout'),
]

urlpatterns = [
    path('', include(auth_urls)),
    path('', include(router_v1.urls)),
]