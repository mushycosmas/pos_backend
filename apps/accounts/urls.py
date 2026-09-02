from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, LoginView


router = DefaultRouter()

router.register(
    'users',
    UserViewSet,
    basename='users'
)


urlpatterns = [
    path(
        'login/',
        LoginView.as_view(),
        name='login'
    ),
]

urlpatterns += router.urls