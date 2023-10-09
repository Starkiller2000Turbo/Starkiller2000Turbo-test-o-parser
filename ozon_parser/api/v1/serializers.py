from rest_framework import serializers

from products.models import Product


class ProductSerializer(serializers.ModelSerializer):
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
        )
        extra_kwargs = {
            'ozon_id': {'write_only': True},
        }
