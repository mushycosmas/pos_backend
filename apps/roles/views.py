from django.contrib.auth.models import Permission
from django.db.models import Count, Q

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import (
    ModelViewSet,
    ReadOnlyModelViewSet,
)

from .models import Role
from .serializers import (
    PermissionSerializer,
    RoleSerializer,
)


# ==============================================================
# ROLE VIEWSET
# ==============================================================

class RoleViewSet(ModelViewSet):
    """
    API endpoint for managing application roles.

    User -> Role relationship will be added later.

    Endpoints:

        GET     /api/v1/roles/
        POST    /api/v1/roles/

        GET     /api/v1/roles/{id}/
        PUT     /api/v1/roles/{id}/
        PATCH   /api/v1/roles/{id}/
        DELETE  /api/v1/roles/{id}/

        GET     /api/v1/roles/{id}/permissions/
        POST    /api/v1/roles/{id}/permissions/

        DELETE  /api/v1/roles/{id}/permissions/{permission_id}/

        GET     /api/v1/roles/{id}/users/

        POST    /api/v1/roles/{id}/activate/
        POST    /api/v1/roles/{id}/deactivate/
    """

    serializer_class = RoleSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    # ==========================================================
    # QUERYSET
    # ==========================================================

    def get_queryset(self):
        """
        Return roles with their permissions and permission count.

        IMPORTANT:
        The User -> Role relationship does not exist yet.

        Therefore we DO NOT use:

            Count("users")

        User count will be implemented after the User model
        is connected to Role.
        """

        queryset = (
            Role.objects
            .prefetch_related(
                "permissions",
            )
            .annotate(
                permission_count_annotation=Count(
                    "permissions",
                    distinct=True,
                )
            )
        )

        # ------------------------------------------------------
        # SEARCH
        # ------------------------------------------------------

        search = self.request.query_params.get(
            "search"
        )

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(code__icontains=search)
                | Q(description__icontains=search)
            )

        # ------------------------------------------------------
        # ACTIVE / INACTIVE FILTER
        # ------------------------------------------------------

        is_active = self.request.query_params.get(
            "is_active"
        )

        if is_active is not None:

            active_value = (
                is_active.lower()
                in [
                    "true",
                    "1",
                    "yes",
                ]
            )

            queryset = queryset.filter(
                is_active=active_value
            )

        return queryset

    # ==========================================================
    # ROLE PERMISSIONS
    # ==========================================================

    @action(
        detail=True,
        methods=["get", "post"],
        url_path="permissions",
    )
    def permissions(
        self,
        request,
        pk=None,
    ):
        """
        GET:
            Return all permissions assigned to the role.

        POST:
            Replace all permissions assigned to the role.

        GET:
            /api/v1/roles/{id}/permissions/

        POST:
            /api/v1/roles/{id}/permissions/

        POST body:

            {
                "permission_ids": [1, 2, 3]
            }
        """

        role = self.get_object()

        # ======================================================
        # GET ROLE PERMISSIONS
        # ======================================================

        if request.method == "GET":

            permissions = (
                role.permissions
                .select_related(
                    "content_type",
                )
                .all()
            )

            serializer = PermissionSerializer(
                permissions,
                many=True,
            )

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )

        # ======================================================
        # POST - ASSIGN PERMISSIONS
        # ======================================================

        permission_ids = request.data.get(
            "permission_ids",
            [],
        )

        # ------------------------------------------------------
        # Validate permission_ids
        # ------------------------------------------------------

        if not isinstance(
            permission_ids,
            list,
        ):
            return Response(
                {
                    "detail": (
                        "permission_ids must be a list."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------------------------------------------
        # Remove duplicate IDs
        # ------------------------------------------------------

        permission_ids = list(
            dict.fromkeys(
                permission_ids
            )
        )

        # ------------------------------------------------------
        # Empty list = remove all permissions
        # ------------------------------------------------------

        if not permission_ids:

            role.permissions.clear()

            role.refresh_from_db()

            return Response(
                self.get_serializer(
                    role
                ).data,
                status=status.HTTP_200_OK,
            )

        # ------------------------------------------------------
        # Get permissions
        # ------------------------------------------------------

        permissions = Permission.objects.filter(
            id__in=permission_ids
        )

        # ------------------------------------------------------
        # Validate all permission IDs
        # ------------------------------------------------------

        if permissions.count() != len(
            permission_ids
        ):

            return Response(
                {
                    "detail": (
                        "One or more permission IDs "
                        "are invalid."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------------------------------------------
        # Replace role permissions
        # ------------------------------------------------------

        role.permissions.set(
            permissions
        )

        role.refresh_from_db()

        return Response(
            self.get_serializer(
                role
            ).data,
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # REMOVE SINGLE PERMISSION
    # ==========================================================

    @action(
        detail=True,
        methods=["delete"],
        url_path=(
            r"permissions/(?P<permission_id>[^/.]+)"
        ),
    )
    def remove_permission(
        self,
        request,
        pk=None,
        permission_id=None,
    ):
        """
        Remove one permission from a role.

        Example:

            DELETE
            /api/v1/roles/1/permissions/5/
        """

        role = self.get_object()

        try:

            permission = Permission.objects.get(
                id=permission_id
            )

        except Permission.DoesNotExist:

            return Response(
                {
                    "detail": (
                        "Permission not found."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        role.permissions.remove(
            permission
        )

        return Response(
            {
                "detail": (
                    "Permission removed successfully."
                )
            },
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # ROLE USERS
    # ==========================================================

    @action(
        detail=True,
        methods=["get"],
        url_path="users",
    )
    def users(
        self,
        request,
        pk=None,
    ):
        """
        Get users assigned to this role.

        User -> Role relationship has not been created yet.

        Therefore this endpoint currently returns an empty list.

        Once the User model is connected to Role, this endpoint
        will return the actual users.
        """

        self.get_object()

        return Response(
            [],
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # ACTIVATE ROLE
    # ==========================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="activate",
    )
    def activate(
        self,
        request,
        pk=None,
    ):
        """
        Activate a role.
        """

        role = self.get_object()

        role.is_active = True

        role.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(
                role
            ).data,
            status=status.HTTP_200_OK,
        )

    # ==========================================================
    # DEACTIVATE ROLE
    # ==========================================================

    @action(
        detail=True,
        methods=["post"],
        url_path="deactivate",
    )
    def deactivate(
        self,
        request,
        pk=None,
    ):
        """
        Deactivate a role.
        """

        role = self.get_object()

        role.is_active = False

        role.save(
            update_fields=[
                "is_active",
                "updated_at",
            ]
        )

        return Response(
            self.get_serializer(
                role
            ).data,
            status=status.HTTP_200_OK,
        )


# ==============================================================
# DJANGO BUILT-IN PERMISSIONS
# ==============================================================

class PermissionViewSet(
    ReadOnlyModelViewSet
):
    """
    Read-only API for Django's built-in Permission model.

    Django automatically creates permissions for registered models:

        add_model
        change_model
        delete_model
        view_model

    We intentionally use Django's built-in Permission model.

    We DO NOT create a custom Permission model.
    """

    serializer_class = PermissionSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    queryset = (
        Permission.objects
        .select_related(
            "content_type",
        )
        .all()
        .order_by(
            "content_type__app_label",
            "content_type__model",
            "codename",
        )
    )

    # ==========================================================
    # QUERYSET FILTERING
    # ==========================================================

    def get_queryset(self):
        queryset = self.queryset

        # ------------------------------------------------------
        # SEARCH
        # ------------------------------------------------------

        search = self.request.query_params.get(
            "search"
        )

        if search:

            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(codename__icontains=search)
                | Q(
                    content_type__model__icontains=search
                )
                | Q(
                    content_type__app_label__icontains=search
                )
            )

        # ------------------------------------------------------
        # MODULE
        # ------------------------------------------------------

        module = self.request.query_params.get(
            "module"
        )

        if module:

            queryset = queryset.filter(
                content_type__app_label=module
            )

        # ------------------------------------------------------
        # ACTION
        # ------------------------------------------------------

        action_name = self.request.query_params.get(
            "action"
        )

        if action_name:

            queryset = queryset.filter(
                codename__startswith=action_name
            )

        return queryset

    # ==========================================================
    # ACTIVE PERMISSIONS
    # ==========================================================

    @action(
        detail=False,
        methods=["get"],
        url_path="active",
    )
    def active(
        self,
        request,
    ):
        """
        Return all available Django permissions.

        Endpoint:

            GET /api/v1/permissions/active/
        """

        permissions = self.get_queryset()

        serializer = self.get_serializer(
            permissions,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )