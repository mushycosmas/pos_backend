from django.db import models
from django.contrib.auth.models import Permission


class Role(models.Model):
    """
    Application Role.

    Each role can have multiple Django permissions.

    Example:
        Administrator
            - add_product
            - change_product
            - delete_product
            - view_product

        Cashier
            - view_product
            - view_sale
            - add_sale
    """

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique machine-readable role code.",
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="custom_roles",
        help_text="Django permissions assigned to this role.",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

        indexes = [
            models.Index(
                fields=["is_active"]
            ),
            models.Index(
                fields=["code"]
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def permission_count(self):
        """
        Number of permissions assigned to this role.
        """
        return self.permissions.count()

    @property
    def user_count(self):
        """
        Number of users assigned to this role.

        This expects the User model to have:

            role = ForeignKey(
                Role,
                related_name="users",
                ...
            )
        """
        if hasattr(self, "users"):
            return self.users.count()

        return 0