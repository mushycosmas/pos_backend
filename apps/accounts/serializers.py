from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):

    role_name = serializers.CharField(
        source="role.name",
        read_only=True
    )

    branch_name = serializers.CharField(
        source="branch.name",
        read_only=True
    )

    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User

        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "role_name",
            "branch",
            "branch_name",
            "permissions",
            "is_active",
            "last_login",
            "last_login_ip",
            "created_at",
            "updated_at",
            "date_joined",
        ]

        read_only_fields = [
            "id",
            "role_name",
            "branch_name",
            "permissions",
            "last_login",
            "last_login_ip",
            "created_at",
            "updated_at",
            "date_joined",
        ]

    def get_permissions(self, obj):
        return sorted(obj.get_all_permissions())


class UserCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True
    )

    class Meta:
        model = User

        fields = [
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "branch",
            "is_active",
        ]

    def create(self, validated_data):

        password = validated_data.pop("password")

        user = User(**validated_data)

        user.set_password(password)

        user.save()

        return user
