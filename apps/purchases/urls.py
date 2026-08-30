from rest_framework.routers import DefaultRouter


from .views import (
    PurchaseViewSet,
    PurchaseItemViewSet
)



router = DefaultRouter()



router.register(
    r'purchases',
    PurchaseViewSet,
    basename='purchases'
)



router.register(
    r'purchase-items',
    PurchaseItemViewSet,
    basename='purchase-items'
)



urlpatterns = router.urls