from rest_framework.routers import DefaultRouter


from .views import (
    PaymentMethodViewSet,
    PaymentViewSet,
    PaymentGatewayViewSet,
    PaymentTransactionLogViewSet,
    PaymentBatchViewSet
)



router = DefaultRouter()



router.register(
    r'payment-methods',
    PaymentMethodViewSet,
    basename='payment-methods'
)



router.register(
    r'payments',
    PaymentViewSet,
    basename='payments'
)



router.register(
    r'payment-gateways',
    PaymentGatewayViewSet,
    basename='payment-gateways'
)



router.register(
    r'payment-logs',
    PaymentTransactionLogViewSet,
    basename='payment-logs'
)



router.register(
    r'payment-batches',
    PaymentBatchViewSet,
    basename='payment-batches'
)



urlpatterns = router.urls