from rest_framework import serializers

from .models import (
    PaymentMethod,
    Payment,
    PaymentGateway,
    PaymentTransactionLog,
    PaymentBatch
)



class PaymentMethodSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentMethod
        fields = '__all__'



class PaymentSerializer(serializers.ModelSerializer):

    company_name = serializers.CharField(
        source='company.name',
        read_only=True
    )

    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True
    )

    class Meta:
        model = Payment
        fields = [
            'id',
            'sale',
            'purchase',
            'company',
            'company_name',
            'branch',
            'branch_name',
            'method',
            'direction',
            'amount',
            'currency',
            'reference',
            'transaction_id',
            'gateway',
            'gateway_response',
            'status',
            'payment_date',
            'notes',
            'processed_by',
            'approved_by',
            'approved_at',
            'created_at',
            'updated_at'
        ]



class PaymentGatewaySerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentGateway
        fields = '__all__'



class PaymentTransactionLogSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentTransactionLog
        fields = '__all__'



class PaymentBatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = PaymentBatch
        fields = '__all__'