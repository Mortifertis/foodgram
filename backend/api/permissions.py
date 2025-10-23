from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        """Allow unsafe methods only for authenticated users."""
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        author_id = getattr(obj, "author_id", None)
        user_id = getattr(request.user, "id", None)
        return author_id == user_id
