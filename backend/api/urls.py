from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter


from .views import (UserViewSet, logout_view)


router_v1 = DefaultRouter()
router_v1.register(r'subscribe',)
router_v1.register(r'users', UserViewSet, basename='users')

auth_urls = [
    path('auth/token/login/', obtain_auth_token, name='login'),
    path('auth/token/logout/', logout_view, name='logout'),
]

urlpatterns = [
    path('', include(auth_urls)),
    path('', include(router_v1.urls)),
]