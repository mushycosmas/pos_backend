from rest_framework import serializers

from .models import Branch


class BranchSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(
        source="company.name",
        read_only=True
    )

    class Meta:
        model = Branch

        fields = [
            "id",
            "company",
            "company_name",
            "name",
            "code",
            "location",
            "phone",
            "email",
            "is_main",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "company",
            "company_name",
            "is_main",
            "created_at",
            "updated_at",
        ]

    def validate_code(self, value):
        value = value.strip().upper()

        if not value:
            raise serializers.ValidationError(
                "Branch code is required."
            )

        if len(value) > 10:
            raise serializers.ValidationError(
                "Branch code cannot exceed 10 characters."
            )

        return value

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Branch name is required."
            )

        return value

    def validate_location(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Branch location is required."
            )

        return value

    def validate_phone(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Branch phone number is required."
            )

        return value