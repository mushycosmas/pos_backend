from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    LoginView,
    MeView,
)


# ============================================================
# ROUTER
# ============================================================

router = DefaultRouter()

router.register(
    'users',
    UserViewSet,
    basename='users'
)


# ============================================================
# URL PATTERNS
# ============================================================

urlpatterns = [

    # --------------------------------------------------------
    # Login
    # --------------------------------------------------------

    path(
        'login/',
        LoginView.as_view(),
        name='login'
    ),

    # --------------------------------------------------------
    # Current authenticated user
    # --------------------------------------------------------

    path(
        'me/',
        MeView.as_view(),
        name='me'
    ),
]


# ============================================================
# ROUTER URLS
# ============================================================

urlpatterns += router.urls