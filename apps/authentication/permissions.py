from rest_framework.permissions import BasePermission


def es_rol(*roles):
    class EsRol(BasePermission):
        def has_permission(self, request, view):
            return request.user.is_authenticated and request.user.rol in roles
    return EsRol
