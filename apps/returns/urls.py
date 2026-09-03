from rest_framework.routers import DefaultRouter

from .views import ReturnViewSet


router = DefaultRouter()

router.register(
    "returns",
    ReturnViewSet,
    basename="returns",
)

urlpatterns = router.urls