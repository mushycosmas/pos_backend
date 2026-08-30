from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from .models import Sale, SaleItem
from .serializers import (
    SaleListSerializer, SaleDetailSerializer, SaleCreateSerializer,
    SaleUpdateSerializer, SaleCancelSerializer, SaleReceiptSerializer,
    SaleSummarySerializer
)
# Remove permissions imports

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['branch', 'status', 'cashier', 'customer', 'created_at']
    search_fields = ['invoice_number', 'customer__name', 'customer__phone']
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']
    
    # Remove get_permissions method entirely
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SaleListSerializer
        # Remove or comment out the retrieve condition
        # elif self.action == 'retrieve':
        #     return SaleDetailSerializer
        elif self.action == 'create':
            return SaleCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return SaleUpdateSerializer
        elif self.action == 'cancel':
            return SaleCancelSerializer
        elif self.action == 'receipt':
            return SaleReceiptSerializer
        elif self.action == 'summary':
            return SaleSummarySerializer
        return SaleDetailSerializer
    
    def get_queryset(self):
        # Remove user role filtering, return all sales
        queryset = Sale.objects.all()
        
        # Apply date filters if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset
    
    # Override retrieve to return 405 Method Not Allowed
    def retrieve(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Method not allowed.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def create(self, request, *args, **kwargs):
        """Create a new sale with items"""
        serializer = self.get_serializer(data=request.data)
        serializer.context.update({
            'request': request,
            'payment_data': request.data.get('payment', None)
        })
        serializer.is_valid(raise_exception=True)
        
        sale = serializer.save()
        
        return Response({
            'success': True,
            'message': 'Sale completed successfully',
            'data': SaleDetailSerializer(sale).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a sale and restore stock"""
        sale = self.get_object()
        serializer = self.get_serializer(data=request.data, context={'sale': sale})
        serializer.is_valid(raise_exception=True)
        
        if sale.status == 'cancelled':
            return Response({
                'success': False,
                'message': 'Sale is already cancelled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Restore stock for each item
            for item in sale.items.all():
                stock = Stock.objects.filter(product=item.product, branch=sale.branch).first()
                if stock:
                    old_quantity = stock.quantity
                    stock.quantity += item.quantity
                    stock.save()
                    
                    StockMovement.objects.create(
                        product=item.product,
                        branch=sale.branch,
                        quantity=item.quantity,
                        previous_quantity=old_quantity,
                        new_quantity=stock.quantity,
                        movement_type='RETURN',
                        reference=f'Cancel Sale {sale.invoice_number}',
                        created_by=request.user,
                        notes=serializer.validated_data.get('reason', '')
                    )
            
            # Update sale status
            sale.status = 'cancelled'
            sale.notes = f"{sale.notes}\nCancelled: {serializer.validated_data.get('reason')}"
            sale.save()
            
            # Cancel payments
            from apps.payments.models import Payment
            payments = Payment.objects.filter(sale=sale)
            for payment in payments:
                payment.status = 'cancelled'
                payment.save()
        
        return Response({
            'success': True,
            'message': 'Sale cancelled successfully',
            'data': SaleDetailSerializer(sale).data
        })
    
    @action(detail=True, methods=['get'])
    def receipt(self, request, pk=None):
        """Generate receipt data for a sale"""
        sale = self.get_object()
        serializer = self.get_serializer(sale)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get sales summary for dashboard"""
        queryset = self.get_queryset()
        
        # Apply date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Calculate summary
        total_sales = sum(sale.total for sale in queryset.filter(status='completed'))
        total_orders = queryset.filter(status='completed').count()
        average_order_value = total_sales / total_orders if total_orders > 0 else 0
        total_tax = sum(sale.tax for sale in queryset.filter(status='completed'))
        total_discount = sum(sale.discount for sale in queryset.filter(status='completed'))
        
        # Top products
        from django.db.models import Sum
        top_products = SaleItem.objects.filter(
            sale__in=queryset.filter(status='completed')
        ).values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total')
        ).order_by('-total_revenue')[:10]
        
        # Sales by hour (for the last 7 days)
        from datetime import timedelta
        seven_days_ago = timezone.now() - timedelta(days=7)
        sales_by_hour = queryset.filter(
            status='completed',
            created_at__gte=seven_days_ago
        ).extra(
            select={'hour': "strftime('%H', created_at)"}
        ).values('hour').annotate(
            total=Sum('total'),
            count=Sum('id')
        ).order_by('hour')
        
        # Sales by day (for the last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        sales_by_day = queryset.filter(
            status='completed',
            created_at__gte=thirty_days_ago
        ).extra(
            select={'day': "strftime('%Y-%m-%d', created_at)"}
        ).values('day').annotate(
            total=Sum('total')
        ).order_by('day')
        
        # Payment methods
        from apps.payments.models import Payment
        payment_methods = Payment.objects.filter(
            sale__in=queryset.filter(status='completed')
        ).values('method').annotate(
            total=Sum('amount'),
            count=Sum('id')
        )
        
        return Response({
            'success': True,
            'data': {
                'total_sales': float(total_sales),
                'total_orders': total_orders,
                'average_order_value': float(average_order_value),
                'total_tax': float(total_tax),
                'total_discount': float(total_discount),
                'top_products': list(top_products),
                'sales_by_hour': {item['hour']: float(item['total']) for item in sales_by_hour},
                'sales_by_day': {item['day']: float(item['total']) for item in sales_by_day},
                'payment_methods': {item['method']: float(item['total']) for item in payment_methods}
            }
        })