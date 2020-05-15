from rest_framework import permissions

from inworkapi.utils import JSendResponse


class IsAuthenticated(permissions.IsAuthenticated):
    message = JSendResponse(
        status=JSendResponse.FAIL, 
        data='Authentication credentials were not provided'
    ).make_json()

    def has_permission(self, request, view):
        return super().has_permission(request, view)


class IsPostOrIsAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        # allow all POST requests
        if request.method == 'POST':
            return True

        # Otherwise, only allow authenticated requests
        # Post Django 1.10, 'is_authenticated' is a read-only attribute
        return request.user and request.user.is_authenticated


class IsAdministrator(permissions.BasePermission):
    message = 'Must have Administrator permissions to perform this action.'

    def has_permission(self, request, view):
        if request.user and not request.user.is_anonymous:
            if not request.user.role:
                return False
            return request.user.is_administrator()
        else:
            return False
