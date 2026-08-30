from rest_framework import serializers
from .models import Supplier


class SupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'phone',
            'email',
            'address',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Supplier name is required."
            )

        return value

    def validate_phone(self, value):
        if value:
            return value.strip()

        return value

    def validate_email(self, value):
        if value:
            return value.strip().lower()

        return value