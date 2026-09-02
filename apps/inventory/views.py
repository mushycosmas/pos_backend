# views.py
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from .models import Stock, StockMovement
from .serializers import (
    StockSerializer,
    StockMovementSerializer
)


class StockViewSet(ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [AllowAny]

    # =========================================================
    # ADD THIS CUSTOM ACTION
    # =========================================================
    @action(detail=True, methods=['patch'], url_path='adjust')
    def adjust_stock(self, request, pk=None):
        """Adjust stock quantity and record the movement."""
        stock = self.get_object()
        
        # Get data from request
        quantity = request.data.get('quantity')
        movement_type = request.data.get('type', '').upper()
        reason = request.data.get('reason', '')
        reference = request.data.get('reference', '')
        notes = request.data.get('notes', '')
        
        # Validate quantity
        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return Response(
                {'error': 'quantity must be a valid integer'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if quantity <= 0:
            return Response(
                {'error': 'quantity must be greater than zero'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate type
        valid_types = ['ADD', 'REMOVE']
        if movement_type not in valid_types:
            return Response(
                {'error': f'type must be one of: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate reason
        if not reason or not reason.strip():
            return Response(
                {'error': 'reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Map to StockMovement types
        type_mapping = {
            'ADD': 'IN',
            'REMOVE': 'OUT',
        }
        movement_type_db = type_mapping.get(movement_type, 'ADJUSTMENT')
        
        with transaction.atomic():
            # Calculate new quantity
            previous_quantity = stock.quantity
            
            if movement_type == 'ADD':
                new_quantity = previous_quantity + quantity
            elif movement_type == 'REMOVE':
                if quantity > previous_quantity:
                    return Response(
                        {'error': f'Insufficient stock. Available: {previous_quantity}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                new_quantity = previous_quantity - quantity
            else:
                new_quantity = quantity
            
            # Update stock
            stock.quantity = new_quantity
            stock.save(update_fields=['quantity', 'last_updated'])
            
            # Create movement record
            movement = StockMovement.objects.create(
                product=stock.product,
                branch=stock.branch,
                quantity=quantity,
                previous_quantity=previous_quantity,
                new_quantity=new_quantity,
                movement_type=movement_type_db,
                reference=reference or '',
                notes=notes or reason,
                created_by=request.user if request.user.is_authenticated else None
            )
        
        # Return response
        serializer = self.get_serializer(stock)
        return Response({
            'stock': serializer.data,
            'movement': StockMovementSerializer(movement).data
        }, status=status.HTTP_200_OK)


class StockMovementViewSet(ModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [AllowAny]