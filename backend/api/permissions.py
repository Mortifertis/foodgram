"""Пользовательские классы разрешений."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Разрешает изменение объектов только их авторам."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if any(
            getattr(user, attr, False)
            for attr in ("is_staff", "is_superuser")
        ):
            return True
        return obj.author == user
