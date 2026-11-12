from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin())


class IsAdminOrITStaff(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_admin() or user.is_it_staff()))


class IsAdminOrReadOnlyITStaff(BasePermission):
    """Admin: full. IT staff: read + operational writes on allowed views. Employees: none here."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_admin():
            return True
        if user.is_it_staff() and request.method in SAFE_METHODS:
            return True
        return False


class IsAuthenticatedEmployee(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated)
