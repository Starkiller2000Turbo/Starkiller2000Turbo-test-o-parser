from rest_framework import serializers

from products.models import Product


class ProductWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для модели избранного."""

    class Meta:
        model = Product
        fields = (
            'name',
            'price',
            'description',
            'image_url',
            'discount',
            'ozon_id',
            'request_date',
        )


class ProductReadSerializer(serializers.ModelSerializer):
    """Сериализатор для модели избранного."""

    class Meta:
        model = Product
        fields = (
            'name',
            'price',
            'description',
            'image_url',
            'discount',
        )


class QuerySerializer(serializers.Serializer):
    """Сериализатор для модели избранного."""

    products_count = serializers.IntegerField(
        max_value=50,
        min_value=0,
        help_text='Amount of products for parsing (default 10)',
    )
