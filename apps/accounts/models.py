
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    phone = models.CharField(
        max_length=15,
        unique=True
    )

    role = models.ForeignKey(
        "roles.Role",
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True
    )

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users"
    )

    is_active = models.BooleanField(default=True)

    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="pos_users",
        related_query_name="pos_user",
    )

    user_permissions = models.ManyToManyField(
        "auth.Permission",
        blank=True,
        related_name="pos_users",
        related_query_name="pos_user",
    )

    def __str__(self):
        return self.username

    def get_all_permissions(self):

        if self.is_superuser:
            from django.contrib.auth.models import Permission

            return {
                f"{p.content_type.app_label}.{p.codename}"
                for p in Permission.objects.select_related(
                    "content_type"
                )
            }

        permissions = set()

        # Role permissions
        if self.role:
            for permission in self.role.permissions.all():
                permissions.add(
                    f"{permission.content_type.app_label}.{permission.codename}"
                )

        # Direct user permissions
        for permission in self.user_permissions.select_related(
            "content_type"
        ):
            permissions.add(
                f"{permission.content_type.app_label}.{permission.codename}"
            )

        # Django groups
        for group in self.groups.all():
            for permission in group.permissions.select_related(
                "content_type"
            ):
                permissions.add(
                    f"{permission.content_type.app_label}.{permission.codename}"
                )

        return permissions

    def has_custom_permission(self, permission):

        if self.is_superuser:
            return True

        return permission in self.get_all_permissions()

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]

