from rest_framework.routers import DefaultRouter

from .views import PaymentMethodViewSet


router = DefaultRouter()

router.register(
    r"payment-methods",
    PaymentMethodViewSet,
    basename="payment-method",
)

urlpatterns = router.urls