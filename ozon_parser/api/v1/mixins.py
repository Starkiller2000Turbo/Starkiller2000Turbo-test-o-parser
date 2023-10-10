from rest_framework import mixins, viewsets


class ListCreateRetrieveViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Миксин с методами POST, GET, RETRIEVE."""

    pass
