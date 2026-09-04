from rest_framework import serializers

from .models import PaymentMethod


class PaymentMethodSerializer(serializers.ModelSerializer):
    payment_type_name = serializers.CharField(
        source="get_payment_type_display",
        read_only=True,
    )

    class Meta:
        model = PaymentMethod

        fields = [
            "id",
            "name",
            "code",
            "payment_type",
            "payment_type_name",
            "provider",
            "is_active",
            "allow_change",
            "transaction_fee",
            "display_order",
            "description",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "payment_type_name",
            "created_at",
            "updated_at",
        ]

    def validate_code(self, value):
        return value.strip().lower().replace(" ", "_")

    def validate_transaction_fee(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "Transaction fee cannot be negative."
            )

        return value