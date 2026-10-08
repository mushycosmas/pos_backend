from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    LoginView,
    MeView,
    CompanyRegistrationView,
)


# ============================================================
# ROUTER
# ============================================================

router = DefaultRouter()

router.register(
    "users",
    UserViewSet,
    basename="users"
)


# ============================================================
# URL PATTERNS
# ============================================================

urlpatterns = [

    # --------------------------------------------------------
    # Login
    # --------------------------------------------------------

    path(
        "login/",
        LoginView.as_view(),
        name="login"
    ),

    # --------------------------------------------------------
    # Company Registration
    # --------------------------------------------------------

    path(
        "register-company/",
        CompanyRegistrationView.as_view(),
        name="register-company"
    ),

    # --------------------------------------------------------
    # Current authenticated user
    # --------------------------------------------------------

    path(
        "me/",
        MeView.as_view(),
        name="me"
    ),
]


# ============================================================
# ROUTER URLS
# ============================================================

urlpatterns += router.urls