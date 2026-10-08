from rest_framework import serializers

from .models import User


# ============================================================
# USER SERIALIZER
# ============================================================

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

    # ========================================================
    # PERMISSIONS
    # ========================================================

    def get_permissions(self, obj):
        return sorted(
            obj.get_all_permissions()
        )


# ============================================================
# USER CREATE SERIALIZER
# ============================================================

class UserCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
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

    # ========================================================
    # CREATE USER
    # ========================================================

    def create(self, validated_data):

        password = validated_data.pop(
            "password"
        )

        user = User(
            **validated_data
        )

        user.set_password(
            password
        )

        user.save()

        return user


# ============================================================
# COMPANY REGISTRATION SERIALIZER
# ============================================================

class CompanyRegistrationSerializer(
    serializers.Serializer
):
    """
    Initial company registration serializer.

    Expected structure:

        {
            "company": {
                ...
            },
            "owner": {
                ...
            }
        }

    The view converts the multipart form data into this
    nested structure before passing it to this serializer.
    """

    company = serializers.DictField(
        required=True
    )

    owner = serializers.DictField(
        required=True
    )

    # ========================================================
    # VALIDATE OWNER
    # ========================================================

    def validate_owner(self, value):

        required_fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "password",
            "password_confirmation",
        ]

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        for field in required_fields:

            field_value = value.get(field)

            if (
                field_value is None
                or str(field_value).strip() == ""
            ):
                raise serializers.ValidationError(
                    {
                        field:
                        f"{field.replace('_', ' ').capitalize()} is required."
                    }
                )

        # ----------------------------------------------------
        # Clean values
        # ----------------------------------------------------

        value["first_name"] = str(
            value["first_name"]
        ).strip()

        value["last_name"] = str(
            value["last_name"]
        ).strip()

        value["username"] = str(
            value["username"]
        ).strip()

        value["email"] = str(
            value["email"]
        ).strip().lower()

        if value.get("phone"):
            value["phone"] = str(
                value["phone"]
            ).strip()

        # ----------------------------------------------------
        # Username validation
        # ----------------------------------------------------

        username = value["username"]

        if len(username) < 3:

            raise serializers.ValidationError(
                {
                    "username":
                    "Username must contain at least 3 characters."
                }
            )

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise serializers.ValidationError(
                {
                    "username":
                    "This username is already registered."
                }
            )

        # ----------------------------------------------------
        # Email validation
        # ----------------------------------------------------

        email = value["email"]

        email_field = serializers.EmailField()

        try:
            email = email_field.run_validation(
                email
            )
        except serializers.ValidationError:
            raise serializers.ValidationError(
                {
                    "email":
                    "Enter a valid email address."
                }
            )

        value["email"] = email

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise serializers.ValidationError(
                {
                    "email":
                    "This email address is already registered."
                }
            )

        # ----------------------------------------------------
        # Password
        # ----------------------------------------------------

        password = value.get(
            "password"
        )

        password_confirmation = value.get(
            "password_confirmation"
        )

        if password != password_confirmation:

            raise serializers.ValidationError(
                {
                    "password_confirmation":
                    "Passwords do not match."
                }
            )

        if len(password) < 8:

            raise serializers.ValidationError(
                {
                    "password":
                    "Password must contain at least 8 characters."
                }
            )

        # ----------------------------------------------------
        # Password should not be username
        # ----------------------------------------------------

        if password.lower() == username.lower():

            raise serializers.ValidationError(
                {
                    "password":
                    "Password cannot be the same as the username."
                }
            )

        return value

    # ========================================================
    # VALIDATE COMPANY
    # ========================================================

    def validate_company(self, value):

        required_fields = [
            "name",
            "phone",
            "email",
            "address",
            "city",
        ]

        # ----------------------------------------------------
        # Required fields
        # ----------------------------------------------------

        for field in required_fields:

            field_value = value.get(field)

            if (
                field_value is None
                or str(field_value).strip() == ""
            ):
                raise serializers.ValidationError(
                    {
                        field:
                        f"{field.replace('_', ' ').capitalize()} is required."
                    }
                )

        # ----------------------------------------------------
        # Clean company values
        # ----------------------------------------------------

        value["name"] = str(
            value["name"]
        ).strip()

        value["phone"] = str(
            value["phone"]
        ).strip()

        value["email"] = str(
            value["email"]
        ).strip().lower()

        value["address"] = str(
            value["address"]
        ).strip()

        value["city"] = str(
            value["city"]
        ).strip()

        if value.get("legal_name"):
            value["legal_name"] = str(
                value["legal_name"]
            ).strip()

        if value.get("registration_number"):
            value["registration_number"] = str(
                value["registration_number"]
            ).strip()

        if value.get("tax_number"):
            value["tax_number"] = str(
                value["tax_number"]
            ).strip()

        if value.get("website"):
            value["website"] = str(
                value["website"]
            ).strip()

        if value.get("country"):
            value["country"] = str(
                value["country"]
            ).strip()

        if value.get("currency"):
            value["currency"] = str(
                value["currency"]
            ).strip().upper()

        if value.get("timezone"):
            value["timezone"] = str(
                value["timezone"]
            ).strip()

        # ----------------------------------------------------
        # Validate company email
        # ----------------------------------------------------

        email_field = serializers.EmailField()

        try:
            value["email"] = email_field.run_validation(
                value["email"]
            )
        except serializers.ValidationError:
            raise serializers.ValidationError(
                {
                    "email":
                    "Enter a valid company email address."
                }
            )

        # ----------------------------------------------------
        # Registration number
        # ----------------------------------------------------
        #
        # If supplied, make sure it is not already used.
        #
        # The actual uniqueness check is also protected by
        # the database model constraint where applicable.
        # ----------------------------------------------------

        registration_number = value.get(
            "registration_number"
        )

        if registration_number:

            from apps.companies.models import Company

            if Company.objects.filter(
                registration_number=registration_number
            ).exists():

                raise serializers.ValidationError(
                    {
                        "registration_number":
                        "This company registration number is already registered."
                    }
                )

        return value

    # ========================================================
    # GLOBAL VALIDATION
    # ========================================================

    def validate(self, attrs):

        company = attrs.get(
            "company",
            {}
        )

        owner = attrs.get(
            "owner",
            {}
        )

        # ----------------------------------------------------
        # Prevent owner and company email from being
        # accidentally different when the business requires
        # the owner email to be the company administrator.
        #
        # We do NOT force them to be the same.
        # ----------------------------------------------------

        if not company.get("currency"):
            company["currency"] = "TZS"

        if not company.get("country"):
            company["country"] = "Tanzania"

        if not company.get("timezone"):
            company["timezone"] = (
                "Africa/Dar_es_Salaam"
            )

        attrs["company"] = company
        attrs["owner"] = owner

        return attrs