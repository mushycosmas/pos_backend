from django.contrib.auth import authenticate
from django.db import transaction

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    CompanyRegistrationSerializer,
)


# ============================================================
# USER VIEWSET
# ============================================================

class UserViewSet(ModelViewSet):

    queryset = User.objects.all().select_related(
        "branch",
        "role",
    )

    permission_classes = [
        AllowAny
    ]

    def get_serializer_class(self):

        if self.action == "create":
            return UserCreateSerializer

        return UserSerializer


# ============================================================
# LOGIN
# ============================================================

class LoginView(APIView):

    permission_classes = [
        AllowAny
    ]

    def post(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        # ----------------------------------------------------
        # VALIDATE INPUT
        # ----------------------------------------------------

        if not username or not password:

            return Response(
                {
                    "detail": "Username and password are required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # AUTHENTICATE
        # ----------------------------------------------------

        user = authenticate(
            request=request,
            username=username,
            password=password
        )

        if user is None:

            return Response(
                {
                    "detail": "Invalid username or password."
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ----------------------------------------------------
        # CHECK ACTIVE
        # ----------------------------------------------------

        if not user.is_active:

            return Response(
                {
                    "detail": "User account is inactive."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # ----------------------------------------------------
        # SAVE LOGIN IP
        # ----------------------------------------------------

        user.last_login_ip = request.META.get(
            "REMOTE_ADDR"
        )

        user.save(
            update_fields=[
                "last_login_ip"
            ]
        )

        # ----------------------------------------------------
        # GENERATE JWT
        # ----------------------------------------------------

        refresh = RefreshToken.for_user(user)

        access_token = refresh.access_token

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return Response(
            {
                "access": str(access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK
        )


# ============================================================
# CURRENT USER
# ============================================================

class MeView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):

        user = request.user

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK
        )


# ============================================================
# COMPANY REGISTRATION
# ============================================================

class CompanyRegistrationView(APIView):

    permission_classes = [
        AllowAny
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
        JSONParser,
    ]

    def post(self, request):

        print("")
        print("=" * 70)
        print("COMPANY REGISTRATION REQUEST")
        print("=" * 70)

        # ----------------------------------------------------
        # DEBUG REQUEST
        # ----------------------------------------------------

        print("Request content type:")
        print(request.content_type)

        print("")
        print("Raw request data:")

        for key, value in request.data.items():

            if key == "owner.password":
                print(key, "********")

            elif key == "owner.password_confirmation":
                print(key, "********")

            else:
                print(key, repr(value))

        print("=" * 70)

        # ----------------------------------------------------
        # EXTRACT COMPANY DATA
        # ----------------------------------------------------

        company_data = {}

        for key, value in request.data.items():

            if key.startswith("company."):

                field_name = key.replace(
                    "company.",
                    "",
                    1
                )

                company_data[field_name] = value

        # ----------------------------------------------------
        # EXTRACT OWNER DATA
        # ----------------------------------------------------

        owner_data = {}

        for key, value in request.data.items():

            if key.startswith("owner."):

                field_name = key.replace(
                    "owner.",
                    "",
                    1
                )

                owner_data[field_name] = value

        # ----------------------------------------------------
        # DEBUG EXTRACTED DATA
        # ----------------------------------------------------

        print("")
        print("EXTRACTED COMPANY DATA:")

        for key, value in company_data.items():

            print(
                key,
                repr(value)
            )

        print("")
        print("EXTRACTED OWNER DATA:")

        for key, value in owner_data.items():

            if key in [
                "password",
                "password_confirmation"
            ]:

                print(
                    key,
                    "********"
                )

            else:

                print(
                    key,
                    repr(value)
                )

        print("=" * 70)

        # ----------------------------------------------------
        # BUILD REGISTRATION DATA
        # ----------------------------------------------------

        registration_data = {
            "company": company_data,
            "owner": owner_data,
        }

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        serializer = CompanyRegistrationSerializer(
            data=registration_data
        )

        if not serializer.is_valid():

            print("")
            print("=" * 70)
            print("REGISTRATION VALIDATION ERROR")
            print("=" * 70)
            print(serializer.errors)
            print("=" * 70)
            print("")

            return Response(
                {
                    "detail": "Registration validation failed.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ----------------------------------------------------
        # VALIDATED DATA
        # ----------------------------------------------------

        validated_data = serializer.validated_data

        company_data = validated_data.get(
            "company",
            {}
        )

        owner_data = validated_data.get(
            "owner",
            {}
        )

        # ----------------------------------------------------
        # CREATE EVERYTHING IN ONE TRANSACTION
        # ----------------------------------------------------

        try:

            with transaction.atomic():

                # ==================================================
                # IMPORT MODELS
                # ==================================================

                from apps.companies.models import Company
                from apps.branches.models import Branch

                # ==================================================
                # CREATE COMPANY
                # ==================================================

                company = Company.objects.create(
                    name=company_data.get("name"),
                    legal_name=company_data.get(
                        "legal_name",
                        ""
                    ),
                    registration_number=company_data.get(
                        "registration_number"
                    ) or None,
                    tax_number=company_data.get(
                        "tax_number",
                        ""
                    ),
                    phone=company_data.get(
                        "phone"
                    ),
                    email=company_data.get(
                        "email"
                    ),
                    website=company_data.get(
                        "website"
                    ) or None,
                    address=company_data.get(
                        "address"
                    ),
                    city=company_data.get(
                        "city"
                    ),
                    country=company_data.get(
                        "country",
                        "Tanzania"
                    ),
                    logo=company_data.get(
                        "logo"
                    ) or None,
                    currency=company_data.get(
                        "currency",
                        "TZS"
                    ),
                    timezone=company_data.get(
                        "timezone",
                        "Africa/Dar_es_Salaam"
                    ),
                    is_active=True,
                )

                # ==================================================
                # CREATE MAIN BRANCH
                # ==================================================

                branch = Branch.objects.create(
                    company=company,
                    name="Main Branch",
                    code="MAIN",
                    location=company_data.get(
                        "address"
                    ),
                    phone=company_data.get(
                        "phone"
                    ),
                    email=company_data.get(
                        "email"
                    ),
                    is_main=True,
                    is_active=True,
                )

                # ==================================================
                # FIND ADMINISTRATOR ROLE
                # ==================================================

                role = None

                # Try Administrator first
                try:

                    role = User._meta.get_field(
                        "role"
                    ).remote_field.model.objects.filter(
                        name__iexact="Administrator"
                    ).first()

                except Exception:

                    role = None

                # Try Admin if Administrator does not exist
                if role is None:

                    try:

                        role = User._meta.get_field(
                            "role"
                        ).remote_field.model.objects.filter(
                            name__iexact="Admin"
                        ).first()

                    except Exception:

                        role = None

                # Try Owner if Admin roles do not exist
                if role is None:

                    try:

                        role = User._meta.get_field(
                            "role"
                        ).remote_field.model.objects.filter(
                            name__iexact="Owner"
                        ).first()

                    except Exception:

                        role = None

                # --------------------------------------------------
                # ROLE REQUIRED
                # --------------------------------------------------

                if role is None:

                    raise ValueError(
                        "Administrator/Admin/Owner role was not found. "
                        "Please create the default role first."
                    )

                # ==================================================
                # CREATE OWNER USER
                # ==================================================

                owner = User(
                    username=owner_data.get(
                        "username"
                    ),
                    first_name=owner_data.get(
                        "first_name"
                    ),
                    last_name=owner_data.get(
                        "last_name"
                    ),
                    email=owner_data.get(
                        "email"
                    ),
                    phone=owner_data.get(
                        "phone",
                        ""
                    ),
                    role=role,
                    branch=branch,
                    is_active=True,
                )

                # --------------------------------------------------
                # SET PASSWORD
                # --------------------------------------------------

                owner.set_password(
                    owner_data.get(
                        "password"
                    )
                )

                # --------------------------------------------------
                # SAVE USER
                # --------------------------------------------------

                owner.save()

                # ==================================================
                # SUCCESS
                # ==================================================

                print("")
                print("=" * 70)
                print("COMPANY REGISTRATION SUCCESSFUL")
                print("=" * 70)
                print(
                    "Company ID:",
                    company.id
                )
                print(
                    "Company:",
                    company.name
                )
                print(
                    "Branch ID:",
                    branch.id
                )
                print(
                    "Branch:",
                    branch.name
                )
                print(
                    "Owner ID:",
                    owner.id
                )
                print(
                    "Username:",
                    owner.username
                )
                print(
                    "Role:",
                    role.name
                )
                print("=" * 70)
                print("")

                return Response(
                    {
                        "message": (
                            "Company registered successfully."
                        ),
                        "company": {
                            "id": company.id,
                            "name": company.name,
                        },
                        "branch": {
                            "id": branch.id,
                            "name": branch.name,
                            "code": branch.code,
                            "is_main": branch.is_main,
                        },
                        "owner": {
                            "id": owner.id,
                            "username": owner.username,
                            "first_name": owner.first_name,
                            "last_name": owner.last_name,
                            "email": owner.email,
                            "role": role.name,
                        },
                    },
                    status=status.HTTP_201_CREATED
                )

        # ----------------------------------------------------
        # VALIDATION / DATABASE ERROR
        # ----------------------------------------------------

        except Exception as error:

            print("")
            print("=" * 70)
            print("COMPANY REGISTRATION DATABASE ERROR")
            print("=" * 70)
            print(
                type(error).__name__,
                ":",
                str(error)
            )
            print("=" * 70)
            print("")

            return Response(
                {
                    "detail": (
                        "Unable to complete company registration."
                    ),
                    "error": str(error),
                },
                status=status.HTTP_400_BAD_REQUEST
            )