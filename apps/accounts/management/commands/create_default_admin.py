
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.roles.models import Role


class Command(BaseCommand):
    help = "Create default POS administrator"

    def handle(self, *args, **options):

        User = get_user_model()

        username = "admin"
        password = "pos123"
        email = "admin@pos.local"

        with transaction.atomic():

            # Find Administrator role
            role = Role.objects.filter(
                name__iexact="Administrator"
            ).first()

            # Fallback to Admin
            if not role:
                role = Role.objects.filter(
                    name__iexact="Admin"
                ).first()

            if not role:
                self.stdout.write(
                    self.style.ERROR(
                        "Administrator/Admin role was not found."
                    )
                )
                return

            # Check if admin already exists
            user = User.objects.filter(
                username=username
            ).first()

            if user:

                # Make sure admin has the correct role
                user.role = role
                user.is_active = True
                user.is_staff = True
                user.is_superuser = True

                user.set_password(password)
                user.save()

                self.stdout.write(
                    self.style.WARNING(
                        "Admin user already exists. Password and permissions updated."
                    )
                )

            else:

                user = User.objects.create(
                    username=username,
                    email=email,
                    first_name="System",
                    last_name="Administrator",
                    role=role,
                    is_active=True,
                    is_staff=True,
                    is_superuser=True,
                )

                user.set_password(password)
                user.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        "Default admin created successfully."
                    )
                )

            self.stdout.write("")
            self.stdout.write(
                self.style.SUCCESS("Username: admin")
            )
            self.stdout.write(
                self.style.SUCCESS("Password: pos123")
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Role: {role.name}"
                )
            )
