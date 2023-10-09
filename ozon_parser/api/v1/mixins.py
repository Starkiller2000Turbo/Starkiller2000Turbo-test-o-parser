from rest_framework import mixins, viewsets

class ListCreateRetrieveViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    pass 