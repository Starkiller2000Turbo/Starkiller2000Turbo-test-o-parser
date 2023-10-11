from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from drf_yasg import openapi
from drf_yasg.utils import no_body, swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import AllowAny

from api.v1.forms import QueryForm
from api.v1.mixins import ListCreateRetrieveViewSet
from api.v1.serializers import ProductReadSerializer, QuerySerializer
from core.constants import OZON_SELLER_1_PRODUCTS
from core.tasks import parse_ozon_seller
from products.models import Product

created_response = openapi.Response(
    'Created N objects',
    ProductReadSerializer(many=True),
)

error_reponse = openapi.Response(
    description="Didn't manage to create objects",
    schema=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'field_name': openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Items(type=openapi.TYPE_STRING),
            ),
        },
    ),
)


class ProductViewSet(ListCreateRetrieveViewSet):
    """Вьюсет, обрабатывающий запросы к продуктам."""

    queryset = Product.objects.all()
    serializer_class = ProductReadSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['PRODUCTS'],
        operation_id='GET PRODUCTS',
        operation_description='Get products list',
    )
    def list(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        """Метод GET для списка товаров.

        Args:
            request: передаваемый запрос.

        Returns:
            Response со списком товаров.
        """
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['PRODUCTS'],
        operation_id='RETRIEVE PRODUCT',
        operation_description='Get product by id',
    )
    def retrieve(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> HttpResponse:
        """Метод RETRIEVE для списка товаров.

        Args:
            request: передаваемый запрос.

        Returns:
            Response со списком товаров.
        """
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['PRODUCTS'],
        operation_id='CREATE PRODUCTS',
        request_body=no_body,
        operation_description='Start parsing from Ozon',
        responses={status.HTTP_200_OK: 'Parsing started'},
        query_serializer=QuerySerializer,
    )
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
        parse_ozon_seller.delay(OZON_SELLER_1_PRODUCTS, int(products_count))
        return HttpResponse(status=status.HTTP_200_OK)
