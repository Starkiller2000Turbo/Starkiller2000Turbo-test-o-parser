from django.contrib import admin

from core.admin import BaseAdmin
from products.models import Product


@admin.register(Product)
class ProductAdmin(BaseAdmin):
    """Способ отображения поста в админке."""

    list_display = (
        'pk',
        'name',
        'price',
        'description',
        'image_url',
        'discount',
        'ozon_id',
    )
    readonly_fields = ('ozon_id',)
    search_fields = ('name',)
    list_filter = ('name', 'price')
