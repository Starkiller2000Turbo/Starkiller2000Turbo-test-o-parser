from datetime import datetime

from bs4 import BeautifulSoup

from bot.tasks import send_message
from core.constants import PRODUCT_PAGE_MARK
from core.utils import (
    count_pages,
    get_html,
    get_new_products,
    get_ozon_product_url,
    get_product,
    start_driver,
)
from ozon_parser.celery import app, logger
from products.models import Product


@app.task
def parse_ozon_seller(url: str, products_count: int) -> None:
    """Парсинг страницы продавца на Ozon.

    Args:
        url: адрес главной страницы.
        products_count: необходимое количество продуктов.

    Returns:
        Response с информацией об ошибках создания или статус-код 201.
    """
    request_date = datetime.now()
    driver = start_driver()
    logger.info('Драйвер запущен')
    pages_count, html = count_pages(driver, url)
    new_ids = get_new_products(driver, url, html, pages_count, products_count)
    logger.info(f'Выбрано новых элементов: {len(new_ids)}')
    saved_products = []
    success_products = 0
    problems = False
    for product_id in new_ids:
        product_html = get_html(
            driver,
            get_ozon_product_url(product_id),
            PRODUCT_PAGE_MARK,
        )
        product_soup = BeautifulSoup(product_html, 'lxml')
        serializer = get_product(product_soup, product_id, request_date)
        if not serializer.is_valid():
            message = (
                'Задача на парсинг товаров с сайта Ozon '
                'завершена преждевременно.'
                f'Товары не сохранены.'
                f'Были замечены следующие ошибки: {serializer.errors}'
            )
            send_message.delay(message)
            logger.error(message)
            problems = True
        else:
            success_products += 1
            saved_products.append(serializer)
    driver.close()
    driver.quit()
    Product.objects.bulk_create(
        [
            Product(**serializer.validated_data)
            for serializer in saved_products
        ],
    )
    if problems:
        message = (
            'Задача на парсинг товаров с сайта Ozon завершена не полностью. '
            f'Сохранено: {saved_products} товаров.'
        )
        send_message.delay(message)
        logger.info(message)
    else:
        message = (
            'Задача на парсинг товаров с сайта Ozon завершена. '
            f'Сохранено: {products_count} товаров.'
        )
        send_message.delay(message)
        logger.info(message)
