"""Custom permissions for the photos API."""

from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request


class IsOwnerOrReadOnly(BasePermission):
    """Allow read access to anyone, write access only to the object owner."""

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user
