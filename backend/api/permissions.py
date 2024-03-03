from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Дает доступ к объекту только автору.

    Чтение доступно всем пользователям.
    """

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)


class IsAuthor(permissions.BasePermission):
    """Дает доступ только автору."""
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
