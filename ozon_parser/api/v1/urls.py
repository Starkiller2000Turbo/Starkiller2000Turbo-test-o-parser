from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.v1.views import ProductViewSet

app_name = '%(app_label)s'

router = DefaultRouter()

router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
