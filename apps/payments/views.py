from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny


from .models import (
    PaymentMethod,
    Payment,
    PaymentGateway,
    PaymentTransactionLog,
    PaymentBatch
)


from .serializers import (
    PaymentMethodSerializer,
    PaymentSerializer,
    PaymentGatewaySerializer,
    PaymentTransactionLogSerializer,
    PaymentBatchSerializer
)



class PaymentMethodViewSet(ModelViewSet):

    queryset = PaymentMethod.objects.all()

    serializer_class = PaymentMethodSerializer

    permission_classes = [
        AllowAny
    ]



class PaymentViewSet(ModelViewSet):

    queryset = Payment.objects.all()

    serializer_class = PaymentSerializer

    permission_classes = [
        AllowAny
    ]



class PaymentGatewayViewSet(ModelViewSet):

    queryset = PaymentGateway.objects.all()

    serializer_class = PaymentGatewaySerializer

    permission_classes = [
        AllowAny
    ]



class PaymentTransactionLogViewSet(ModelViewSet):

    queryset = PaymentTransactionLog.objects.all()

    serializer_class = PaymentTransactionLogSerializer

    permission_classes = [
        AllowAny
    ]



class PaymentBatchViewSet(ModelViewSet):

    queryset = PaymentBatch.objects.all()

    serializer_class = PaymentBatchSerializer

    permission_classes = [
        AllowAny
    ]