from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(ModelViewSet):

    queryset = Customer.objects.select_related(
        'company',
        'branch'
    ).all()

    serializer_class = CustomerSerializer

    permission_classes = [
        AllowAny
    ]


    @action(
        detail=True,
        methods=['get'],
        url_path='sales'
    )
    def sales_history(self, request, pk=None):

        customer = self.get_object()

        sales = customer.sales.all()

        data = []

        for sale in sales:
            data.append({
                "invoice": sale.invoice_number,
                "total": sale.total,
                "status": sale.status,
                "date": sale.created_at
            })


        return Response(data)