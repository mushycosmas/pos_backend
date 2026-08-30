from rest_framework import serializers
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):

    customer_type_display = serializers.CharField(
        source='get_customer_type_display',
        read_only=True
    )

    company_name = serializers.CharField(
        source='company.name',
        read_only=True
    )

    branch_name = serializers.CharField(
        source='branch.name',
        read_only=True
    )


    class Meta:
        model = Customer

        fields = [
            'id',
            'name',
            'phone',
            'email',
            'address',
            'customer_type',
            'customer_type_display',
            'tax_number',

            'credit_limit',
            'current_balance',

            'company',
            'company_name',

            'branch',
            'branch_name',

            'is_active',

            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'current_balance',
            'created_at',
            'updated_at',
        ]