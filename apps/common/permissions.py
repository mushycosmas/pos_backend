from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Permission class for admin users only.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsOwner(permissions.BasePermission):
    """
    Permission class for business owner users only.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'owner'
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role == 'owner'


class IsManager(permissions.BasePermission):
    """
    Permission class for manager users only.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'manager'
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role == 'manager'


class IsCashier(permissions.BasePermission):
    """
    Permission class for cashier users only.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'cashier'
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role == 'cashier'


class IsStorekeeper(permissions.BasePermission):
    """
    Permission class for storekeeper users only.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'storekeeper'
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role == 'storekeeper'


class IsAdminOrOwner(permissions.BasePermission):
    """
    Permission class for admin or owner users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner']


class IsAdminOrManager(permissions.BasePermission):
    """
    Permission class for admin or manager users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'manager']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'manager']


class IsAdminOwnerOrManager(permissions.BasePermission):
    """
    Permission class for admin, owner, or manager users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager']


class IsManagerOrCashier(permissions.BasePermission):
    """
    Permission class for manager or cashier users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['manager', 'cashier']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['manager', 'cashier']


class IsStaff(permissions.BasePermission):
    """
    Permission class for any staff user (non-admin).
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['owner', 'manager', 'cashier', 'storekeeper']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['owner', 'manager', 'cashier', 'storekeeper']


class IsSameBranch(permissions.BasePermission):
    """
    Permission class to check if user belongs to the same branch as the object.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if object has branch attribute
        if hasattr(obj, 'branch'):
            return obj.branch == request.user.branch
        # Check if object has branch_id attribute
        elif hasattr(obj, 'branch_id'):
            return obj.branch_id == request.user.branch_id
        # For admin users, allow access
        elif request.user.role in ['admin', 'owner']:
            return True
        
        return False


class IsOwnerOrManagerOfBranch(permissions.BasePermission):
    """
    Permission class for owner or manager of the branch.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['owner', 'manager']
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role in ['admin', 'owner']:
            return True
        
        # For managers, check branch
        if hasattr(obj, 'branch'):
            return obj.branch == request.user.branch
        elif hasattr(obj, 'branch_id'):
            return obj.branch_id == request.user.branch_id
        
        return False


class HasCompanyAccess(permissions.BasePermission):
    """
    Permission class to check if user has access to the company.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role in ['admin']:
            return True
        
        # Check if object has company attribute
        if hasattr(obj, 'company'):
            return obj.company == request.user.company
        elif hasattr(obj, 'company_id'):
            return obj.company_id == request.user.company_id
        
        return True


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Permission class for users to access their own data or admin access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['admin', 'owner']:
            return True
        
        # Check if object is a user and matches the current user
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        
        # Check if object has user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class ReadOnly(permissions.BasePermission):
    """
    Permission class for read-only access.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS are GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False


class ReadOnlyOrAdmin(permissions.BasePermission):
    """
    Permission class for read-only access for all users, but admin can write.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.role in ['admin', 'owner']


class AdminOrReadOnly(permissions.BasePermission):
    """
    Permission class for admin write access, others read-only.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.role in ['admin', 'owner']


class IsAllowedToProcessPayment(permissions.BasePermission):
    """
    Permission class to check if user can process payments.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager', 'cashier']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager', 'cashier']


class IsAllowedToManageInventory(permissions.BasePermission):
    """
    Permission class to check if user can manage inventory.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager', 'storekeeper']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager', 'storekeeper']


class IsAllowedToManageSuppliers(permissions.BasePermission):
    """
    Permission class to check if user can manage suppliers.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager']


class IsAllowedToViewReports(permissions.BasePermission):
    """
    Permission class to check if user can view reports.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager']


class IsAdminOrOwnerOrManagerOrCashier(permissions.BasePermission):
    """
    Permission class for admin, owner, manager, or cashier users.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager', 'cashier']
    
    def has_object_permission(self, request, view, obj):
        return request.user and request.user.is_authenticated and request.user.role in ['admin', 'owner', 'manager', 'cashier']