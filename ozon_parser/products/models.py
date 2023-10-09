from django.db import models


class Product(models.Model):
    """Модель продукта."""

    name = models.CharField(max_length=250, verbose_name='имя')
    price = models.IntegerField(verbose_name='цена')
    description = models.TextField(
        max_length=5000,
        verbose_name='описание',
        blank=True,
        null=True,
    )
    image_url = models.URLField(verbose_name='адрес картинки')
    discount = models.CharField(
        max_length=50,
        verbose_name='скидка',
        blank=True,
        null=True,
    )
    ozon_id = models.IntegerField(verbose_name='id продукта', unique=True)
    request_date = models.DateTimeField()

    class Meta:
        ordering = ('name', 'price')
        verbose_name = 'продукт'
        verbose_name_plural = 'продукты'

    def __str__(self) -> str:
        """Представление модели при выводе.

        Returns:
            Строка поля name, используемого для представления модели.
        """
        return self.name
