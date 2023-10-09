from django.http import HttpRequest, HttpResponse, JsonResponse
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from api.v1.forms import QueryForm
from api.v1.serializers import ProductSerializer
from core.constants import OZON_SELLER_1_PRODUCTS
from core.utils import parse_ozon_seller
from products.models import Product


class ProductViewSet(viewsets.ModelViewSet):
    """Вьюсет, обрабатывающий запросы к продуктам."""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def create(self, request: HttpRequest) -> HttpResponse:
        """Метод POST.

        Args:
            request: передаваемый запрос.

        Returns:
            Информацию об ошибках или статус-код 201.
        """
        products_count = request.GET.get('products_count')
        if products_count:
            query = QueryForm({'products_count': products_count})
            if not query.is_valid():
                return JsonResponse(query.errors)
        else:
            products_count = '10'
        return parse_ozon_seller(OZON_SELLER_1_PRODUCTS, int(products_count))
