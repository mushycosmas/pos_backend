from django.db import models
from django.core.files.storage import default_storage


class Company(models.Model):
    name = models.CharField(max_length=200)

    legal_name = models.CharField(
        max_length=200,
        blank=True
    )

    registration_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )

    tax_number = models.CharField(
        max_length=50,
        blank=True
    )

    phone = models.CharField(
        max_length=15
    )

    email = models.EmailField()

    website = models.URLField(
        blank=True,
        null=True
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100
    )

    country = models.CharField(
        max_length=100,
        default="Tanzania"
    )

    logo = models.ImageField(
        upload_to="company/",
        blank=True,
        null=True
    )

    currency = models.CharField(
        max_length=3,
        default="TZS"
    )

    timezone = models.CharField(
        max_length=50,
        default="Africa/Dar_es_Salaam"
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def save(self, *args, **kwargs):
        """
        Save the company and remove the previous logo
        when a new logo is uploaded.
        """

        old_logo_name = None

        # If this company already exists, get the old logo
        if self.pk:
            try:
                old_company = Company.objects.get(pk=self.pk)

                if old_company.logo:
                    old_logo_name = old_company.logo.name

            except Company.DoesNotExist:
                pass

        # Save the company first
        super().save(*args, **kwargs)

        # Delete old logo if a new logo was uploaded
        if (
            old_logo_name
            and self.logo
            and old_logo_name != self.logo.name
        ):
            if default_storage.exists(old_logo_name):
                default_storage.delete(old_logo_name)

    def delete(self, *args, **kwargs):
        """
        Delete the company and its logo file.
        """

        logo_name = None

        if self.logo:
            logo_name = self.logo.name

        # Delete database record
        super().delete(*args, **kwargs)

        # Delete physical logo file
        if logo_name:
            if default_storage.exists(logo_name):
                default_storage.delete(logo_name)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "companies"
        ordering = ["name"]
        verbose_name = "Company"
        verbose_name_plural = "Companies"