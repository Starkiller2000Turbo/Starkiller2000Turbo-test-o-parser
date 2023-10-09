from django.http import HttpRequest
from rest_framework import permissions, viewsets


class ReadOnly(permissions.BasePermission):
    """Разрешение только на чтение."""

    def has_permission(
        self,
        request: HttpRequest,
        view: viewsets.ModelViewSet,
    ) -> bool:
        """Проверка безопасности запроса.

        Args:
            request: Передаваемый запрос.
            view: ViewSet, для которого проверяется разрешение.

        Returns:
            True или False в зависимости от наличия разрешения.
        """
        return request.method in permissions.SAFE_METHODS
