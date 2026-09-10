from django.contrib.auth.models import AbstractUser, Permission
from django.db import models


class User(AbstractUser):

    # =====================================================
    # PHONE
    # =====================================================

    phone = models.CharField(
        max_length=15,
        unique=True,
    )

    # =====================================================
    # ROLE
    #
    # Python:
    #     user.role
    #
    # Database:
    #     users.role_id
    # =====================================================

    role = models.ForeignKey(
        "roles.Role",
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
    )

    # =====================================================
    # BRANCH
    # =====================================================

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.SET_NULL,
        related_name="users",
        null=True,
        blank=True,
    )

    # =====================================================
    # STATUS
    # =====================================================

    is_active = models.BooleanField(
        default=True,
    )

    # =====================================================
    # LOGIN IP
    # =====================================================

    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # =====================================================
    # DJANGO GROUPS
    # =====================================================

    groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="pos_users",
        related_query_name="pos_user",
    )

    # =====================================================
    # DIRECT USER PERMISSIONS
    # =====================================================

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        related_name="pos_users",
        related_query_name="pos_user",
    )

    # =====================================================
    # STRING REPRESENTATION
    # =====================================================

    def __str__(self):
        return self.username

    # =====================================================
    # GET ALL PERMISSIONS
    #
    # Combines:
    # 1. Superuser permissions
    # 2. Role permissions
    # 3. Direct user permissions
    # 4. Django group permissions
    # =====================================================

    def get_all_permissions(self):

        # -------------------------------------------------
        # SUPERUSER
        # -------------------------------------------------

        if self.is_superuser:
            return {
                f"{permission.content_type.app_label}."
                f"{permission.codename}"
                for permission in Permission.objects.select_related(
                    "content_type"
                )
            }

        permissions = set()

        # -------------------------------------------------
        # ROLE PERMISSIONS
        # -------------------------------------------------

        if self.role_id:
            role_permissions = self.role.permissions.select_related(
                "content_type"
            )

            for permission in role_permissions:
                permissions.add(
                    f"{permission.content_type.app_label}."
                    f"{permission.codename}"
                )

        # -------------------------------------------------
        # DIRECT USER PERMISSIONS
        # -------------------------------------------------

        user_permissions = self.user_permissions.select_related(
            "content_type"
        )

        for permission in user_permissions:
            permissions.add(
                f"{permission.content_type.app_label}."
                f"{permission.codename}"
            )

        # -------------------------------------------------
        # GROUP PERMISSIONS
        # -------------------------------------------------

        for group in self.groups.prefetch_related(
            "permissions__content_type"
        ):
            for permission in group.permissions.all():
                permissions.add(
                    f"{permission.content_type.app_label}."
                    f"{permission.codename}"
                )

        return permissions

    # =====================================================
    # CHECK CUSTOM PERMISSION
    # =====================================================

    def has_custom_permission(self, permission):

        if self.is_superuser:
            return True

        return permission in self.get_all_permissions()

    # =====================================================
    # META
    # =====================================================

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]
