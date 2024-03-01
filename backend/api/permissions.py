from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Дает доступ к объекту только автору.
    Чтение доступно всем пользователям.
    """

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)


class IsAuthor(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Дает доступ только администраторам
    и сотрудникам административной части.
    """

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_staff)
