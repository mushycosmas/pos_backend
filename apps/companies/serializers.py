from rest_framework import serializers
from .models import Company


class CompanySerializer(serializers.ModelSerializer):

    class Meta:
        model = Company

        fields = [
            'id',
            'name',
            'legal_name',
            'registration_number',
            'tax_number',
            'phone',
            'email',
            'website',
            'address',
            'city',
            'country',
            'logo',
            'currency',
            'is_active',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]