from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from apps.accounts.models import Permission
from apps.roles.models import Role


# ============================================================
# CUSTOM PERMISSION CONSTANTS
# ============================================================

DASHBOARD_VIEW = "dashboard.view_dashboard"

REPORTS_VIEW = "reports.view_report"

SETTINGS_VIEW = "settings.view_setting"
SETTINGS_CHANGE = "settings.change_setting"


# ============================================================
# CUSTOM PERMISSIONS ONLY
# ============================================================
#
# DO NOT add permissions here for real Django models such as:
#
# products.view_product
# sales.view_sale
# customers.view_customer
# expenses.view_expense
# suppliers.view_supplier
# roles.view_role
# paymentmethods.view_paymentmethod
#
# Those already exist in your permission table.
#
# ============================================================

CUSTOM_PERMISSIONS = {
    "dashboard": {
        "view_dashboard": "Can view dashboard",
    },
    "reports": {
        "view_report": "Can view reports",
    },
    "settings": {
        "view_setting": "Can view settings",
        "change_setting": "Can change settings",
    },
}


# ============================================================
# ROLE -> CUSTOM PERMISSIONS
# ============================================================

CUSTOM_ROLE_PERMISSIONS = {
    "Administrator": {
        DASHBOARD_VIEW,
        REPORTS_VIEW,
        SETTINGS_VIEW,
        SETTINGS_CHANGE,
    },

    "Admin": {
        DASHBOARD_VIEW,
        REPORTS_VIEW,
        SETTINGS_VIEW,
        SETTINGS_CHANGE,
    },

    "Owner": {
        DASHBOARD_VIEW,
        REPORTS_VIEW,
        SETTINGS_VIEW,
        SETTINGS_CHANGE,
    },

    "Manager": {
        DASHBOARD_VIEW,
        REPORTS_VIEW,
        SETTINGS_VIEW,
        SETTINGS_CHANGE,
    },

    "Cashier": {
        DASHBOARD_VIEW,
    },

    "Storekeeper": {
        DASHBOARD_VIEW,
    },
}


class Command(BaseCommand):
    """
    Create only custom POS permissions and assign them to roles.

    Existing model permissions are NOT recreated.

    The command is safe to run repeatedly.
    """

    help = "Create and assign custom POS permissions."

    # ========================================================
    # HANDLE
    # ========================================================

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "=" * 60
            )
        )
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "          CUSTOM POS PERMISSIONS"
            )
        )
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "=" * 60
            )
        )
        self.stdout.write("")

        self.created_count = 0
        self.existing_count = 0
        self.assignment_count = 0

        # ----------------------------------------------------
        # STEP 1: CREATE CUSTOM PERMISSIONS
        # ----------------------------------------------------

        permission_map = self.create_custom_permissions()

        self.stdout.write("")

        # ----------------------------------------------------
        # STEP 2: ASSIGN PERMISSIONS TO ROLES
        # ----------------------------------------------------

        self.assign_role_permissions(permission_map)

        self.stdout.write("")

        # ----------------------------------------------------
        # STEP 3: SUMMARY
        # ----------------------------------------------------

        self.print_summary()

    # ========================================================
    # CREATE CUSTOM PERMISSIONS
    # ========================================================

    def create_custom_permissions(self):

        permission_map = {}

        for app_label, permissions in CUSTOM_PERMISSIONS.items():

            content_type = self.get_custom_content_type(
                app_label
            )

            for codename, permission_name in permissions.items():

                permission, created = (
                    Permission.objects.get_or_create(
                        content_type=content_type,
                        codename=codename,
                        defaults={
                            "name": permission_name,
                        },
                    )
                )

                # ------------------------------------------------
                # Keep permission name correct
                # ------------------------------------------------

                if permission.name != permission_name:

                    permission.name = permission_name

                    permission.save(
                        update_fields=["name"]
                    )

                permission_key = (
                    f"{app_label}.{codename}"
                )

                permission_map[
                    permission_key
                ] = permission

                # ------------------------------------------------
                # Console output
                # ------------------------------------------------

                if created:

                    self.created_count += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  + Created: "
                            f"{permission_key}"
                        )
                    )

                else:

                    self.existing_count += 1

                    self.stdout.write(
                        f"  = Exists:  "
                        f"{permission_key}"
                    )

        return permission_map

    # ========================================================
    # CUSTOM CONTENT TYPE
    # ========================================================

    def get_custom_content_type(self, app_label):

        content_type, created = (
            ContentType.objects.get_or_create(
                app_label=app_label,
                model=app_label,
            )
        )

        return content_type

    # ========================================================
    # ASSIGN PERMISSIONS TO ROLES
    # ========================================================

    def assign_role_permissions(self, permission_map):

        for role_name, permission_names in (
            CUSTOM_ROLE_PERMISSIONS.items()
        ):

            roles = Role.objects.filter(
                name__iexact=role_name
            )

            if not roles.exists():

                self.stdout.write(
                    self.style.WARNING(
                        f"  ! Role not found: "
                        f"{role_name}"
                    )
                )

                continue

            for role in roles:

                permission_objects = []

                for permission_name in permission_names:

                    permission = permission_map.get(
                        permission_name
                    )

                    if permission is None:

                        self.stdout.write(
                            self.style.WARNING(
                                f"  ! Permission not found: "
                                f"{permission_name}"
                            )
                        )

                        continue

                    permission_objects.append(
                        permission
                    )

                if not permission_objects:

                    continue

                # ------------------------------------------------
                # Check existing permissions first
                # ------------------------------------------------

                existing_ids = set(
                    role.permissions.filter(
                        id__in=[
                            permission.id
                            for permission
                            in permission_objects
                        ]
                    ).values_list(
                        "id",
                        flat=True,
                    )
                )

                # ------------------------------------------------
                # Add only missing permissions
                # ------------------------------------------------

                role.permissions.add(
                    *permission_objects
                )

                new_count = (
                    len(permission_objects)
                    - len(existing_ids)
                )

                self.assignment_count += new_count

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ {role.name}: "
                        f"{new_count} new custom "
                        f"permission(s)"
                    )
                )

    # ========================================================
    # SUMMARY
    # ========================================================

    def print_summary(self):

        self.stdout.write("")

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "=" * 60
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Custom permissions created : "
                f"{self.created_count}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Custom permissions existing: "
                f"{self.existing_count}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"New role assignments        : "
                f"{self.assignment_count}"
            )
        )

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                "=" * 60
            )
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "Custom POS permission setup completed."
            )
        )

        self.stdout.write("")