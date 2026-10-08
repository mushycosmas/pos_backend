from django.db import models

from apps.companies.models import Company


class Branch(models.Model):

    # ============================================================
    # COMPANY
    # ============================================================

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="branches",
        null=True,
        blank=True,
    )

    # ============================================================
    # BASIC INFORMATION
    # ============================================================

    name = models.CharField(
        max_length=100
    )

    code = models.CharField(
        max_length=10
    )

    location = models.CharField(
        max_length=200
    )

    phone = models.CharField(
        max_length=15
    )

    email = models.EmailField(
        blank=True,
        null=True,
    )

    # ============================================================
    # BRANCH STATUS
    # ============================================================

    is_main = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    # ============================================================
    # TIMESTAMPS
    # ============================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # ============================================================
    # STRING REPRESENTATION
    # ============================================================

    def __str__(self):

        if self.company:
            return f"{self.name} - {self.company.name}"

        return self.name

    # ============================================================
    # META
    # ============================================================

    class Meta:

        db_table = "branches"

        ordering = [
            "name"
        ]

        constraints = [

            models.UniqueConstraint(
                fields=[
                    "company",
                    "code"
                ],
                name="unique_branch_code_per_company",
            ),

        ]