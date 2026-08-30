from rest_framework.routers import DefaultRouter

from .views import (
    StockViewSet,
    StockMovementViewSet
)


router = DefaultRouter()


router.register(
    r'stocks',
    StockViewSet,
    basename='stocks'
)


router.register(
    r'stock-movements',
    StockMovementViewSet,
    basename='stock-movements'
)


urlpatterns = router.urls