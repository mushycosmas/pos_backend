from django.contrib.auth.models import Permission
from rest_framework import serializers

from .models import Role


class PermissionSerializer(serializers.ModelSerializer):
    content_type_name = serializers.CharField(
        source="content_type.model",
        read_only=True,
    )

    app_label = serializers.CharField(
        source="content_type.app_label",
        read_only=True,
    )

    class Meta:
        model = Permission

        fields = [
            "id",
            "name",
            "codename",
            "content_type",
            "content_type_name",
            "app_label",
        ]

        read_only_fields = [
            "id",
            "name",
            "codename",
            "content_type",
            "content_type_name",
            "app_label",
        ]


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(
        many=True,
        read_only=True,
    )

    permission_ids = serializers.PrimaryKeyRelatedField(
        source="permissions",
        many=True,
        queryset=Permission.objects.all(),
        write_only=True,
        required=False,
    )

    permission_count = serializers.IntegerField(
        source="permission_count_annotation",
        read_only=True,
    )

    # User is not connected to Role yet.
    # This will be implemented after the User -> Role migration.
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Role

        fields = [
            "id",
            "name",
            "code",
            "description",
            "permissions",
            "permission_ids",
            "permission_count",
            "user_count",
            "is_active",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "permissions",
            "permission_count",
            "user_count",
            "created_at",
            "updated_at",
        ]

    def get_user_count(self, obj):
        """
        User -> Role relationship has not been created yet.
        Return 0 until the relationship is added.
        """
        return 0

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Role name cannot be empty."
            )

        return value

    def validate_code(self, value):
        value = value.strip().lower()

        if not value:
            raise serializers.ValidationError(
                "Role code cannot be empty."
            )

        value = value.replace(" ", "_")

        return value

    def create(self, validated_data):
        permissions = validated_data.pop(
            "permissions",
            []
        )

        role = Role.objects.create(
            **validated_data
        )

        if permissions:
            role.permissions.set(permissions)

        return role

    def update(self, instance, validated_data):
        permissions = validated_data.pop(
            "permissions",
            None
        )

        instance = super().update(
            instance,
            validated_data
        )

        if permissions is not None:
            instance.permissions.set(
                permissions
            )

        return instance