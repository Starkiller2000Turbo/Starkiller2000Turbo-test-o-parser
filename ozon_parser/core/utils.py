import logging
import re
import unicodedata
from datetime import datetime
from time import sleep
from typing import Any, List, Optional

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from django.http import HttpResponse, JsonResponse
from fake_useragent import UserAgent
from rest_framework import status
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from api.v1.serializers import ProductReadSerializer, ProductWriteSerializer
from bot.bot import CHAT_ID, sync_send_message
from core.constants import (
    DATA_TAGS,
    OZON_PRODUCT_URL,
    PRODUCT_PAGE_MARK,
    SELLER_PAGE_MARK,
)
from products.models import Product

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)


def extend_with_unique(list1: List[Any], list2: List[Any]) -> List[Any]:
    """Метод слияния списков с уникальными элементами.

    Args:
        list1: список уникальных элементов.
        list2: список уникальных элементов.

    Returns:
        Объединенный список уникальных элементов.
    """
    for element in list2:
        if element not in list1:
            list1.append(element)
    return list1


def start_driver() -> uc.Chrome:
    """Метод для создания драйвера Chrome.

    Returns:
        Объект драйвера Chrome.
    """
    options = uc.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--no-sandbox')
    options.add_argument('--user-agent={}'.format(UserAgent().chrome))
    options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    driver = uc.Chrome(
        driver_executable_path=ChromeDriverManager().install(),
        options=options,
    )
    return driver


def get_html(
    driver: webdriver.Chrome,
    url: str,
    css_selector: str = '',
) -> str:
    """Получение html сайта по его url.

    Args:
        url: строка url-адреса.

    Returns:
        html страницы.
    """
    sleep(1)
    driver.get(url)
    if css_selector:
        try:
            wait_delay = 10
            WebDriverWait(driver, wait_delay).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, css_selector),
                ),
            )
            logging.info(f'Страница {url} загрузилась')
            sleep_delay = 3
            sleep(sleep_delay)
        except TimeoutException:
            message = (
                f'Страница {url} загрузилась не до конца.\n'
                'Возможно, будет необходимо вручную убедиться '
                'в качестве записанной информации'
            )
            sync_send_message(CHAT_ID, message)
            logging.warning(message)
    else:
        delay = 5
        sleep(delay)
        logging.info(f'Страница {url} загружалась {delay} секунд')
    html = driver.page_source
    return html


def get_ozon_product_url(product_id: int) -> str:
    """Метод для получения адреса продукта OZON.

    Args:
        product_id: id продукта на сайте OZON.

    Returns:
        URL продукта на сайте OZON.
    """
    return OZON_PRODUCT_URL + str(product_id)


def count_pages(driver: uc.Chrome, url: str) -> int:
    """Функция для определения количества страниц в пагинаторе ozon.

    Args:
        driver: используемый драйвер.
        url: адрес главной страницы.

    Returns:
        Количество страниц в пагинаторе ozon.
    """
    html = get_html(driver, url, SELLER_PAGE_MARK)
    pages_count = int(
        re.search(  # type: ignore[union-attr]
            r'"totalPages":(\d+)',
            html,
        )
        .group(1)
        .strip("'"),
    )
    logging.info(f'Обнаружено страниц: {pages_count}')
    return pages_count


def get_new_products_on_page(
    driver: uc.Chrome,
    url: str,
    created_ids: List[int],
) -> List[int]:
    """Метод получения новых продуктов на странице.

    Args:
        driver: используемый драйвер браузера.
        url: требуемый адрес страницы.
        created_ids: список созданных id объектов.

    Returns:
        Список новых продуктов
        Дополнительно - количество страниц: если count_pages = True.
    """
    html = get_html(driver, url, SELLER_PAGE_MARK)
    soup = BeautifulSoup(html, 'lxml')
    ozon_ids = [
        int(
            re.search(  # type: ignore[union-attr]
                r'(\d+)/',
                item.find('a')['href'],
            ).group(1),
        )
        for item in soup.find(
            DATA_TAGS['products']['tag'],
            {'class': DATA_TAGS['products']['class']},
        ).find_all(
            DATA_TAGS['product']['tag'],
            {'class': DATA_TAGS['product']['class']},
        )
    ]
    return list(filter(lambda id: id not in created_ids, ozon_ids))


def get_new_products(
    driver: uc.Chrome,
    url: str,
    products_count: int,
) -> List[int]:
    """Метод получения новых продуктов на сайте.

    Args:
        driver: используемый драйвер браузера.
        url: адрес главной страницы.
        products_count: необходимое количество новых продуктов.

    Returns:
        Список новых продуктов
    """
    created_ids = list(Product.objects.all().values_list('ozon_id', flat=True))
    logging.info(f'Количество уже существующих товаров: {len(created_ids)}')
    pages_count = count_pages(driver, url)
    new_ids = get_new_products_on_page(
        driver,
        url,
        created_ids,
    )
    logging.info(f'Количество новых элементов на странице: {len(new_ids)}')
    if len(new_ids) >= products_count:
        return new_ids[:products_count]
    else:
        for page in range(2, pages_count + 1):
            added_ids = get_new_products_on_page(
                driver,
                url + f'?page={page}',
                created_ids,
            )
            new_ids = extend_with_unique(new_ids, added_ids)
            logging.info(
                f'Количество новых элементов на странице: {len(new_ids)}',
            )
            if len(new_ids) >= products_count:
                return new_ids[:products_count]
        return new_ids


def get_name(product_soup: BeautifulSoup) -> Optional[str]:
    """Метод получения имени продукта.

    Args:
        product_soup: BeautifulSoup страницы продукта.

    Returns:
        Имя или None, если имя не найдено.
    """
    try:
        name = product_soup.find(
            DATA_TAGS['name']['tag'],
            {'class': DATA_TAGS['name']['class']},
        ).text
    except AttributeError as err:
        logging.info(f'Не удалось получить имя: {err}')
        name = None
    return name


def get_image_url(product_soup: BeautifulSoup) -> Optional[str]:
    """Метод получения адреса картинки продукта.

    Args:
        product_soup: BeautifulSoup страницы продукта.

    Returns:
        Адрес картинки или None, если адрес картинки не найден.
    """
    try:
        image = product_soup.find(
            DATA_TAGS['image']['tag'],
            {'class': DATA_TAGS['image']['class']},
        ).find('img')
        image_url = image['src']
    except (AttributeError, TypeError) as err:
        logging.info(f'Не удалось получить адрес картинки: {err}')
        image_url = None
    return image_url


def get_price(product_soup: BeautifulSoup) -> Optional[str]:
    """Метод получения цены продукта.

    Args:
        product_soup: BeautifulSoup страницы продукта.

    Returns:
        Цену или None, если цена не найдена.
    """
    try:
        price = ''.join(
            product_soup.find(
                DATA_TAGS['price']['tag'],
                {'class': DATA_TAGS['price']['class']},
            ).text.split()[:-1],
        )
    except AttributeError as err:
        logging.info(f'Не удалось получить цену: {err}')
        price = None
    return price


def get_discount(product_soup: BeautifulSoup) -> Optional[str]:
    """Метод получения скидки продукта.

    Args:
        product_soup: BeautifulSoup страницы продукта.

    Returns:
        Скидку или None, если скидка не найдена.
    """
    try:
        discount = (
            product_soup.find(
                DATA_TAGS['discount']['tag'],
                {'class': DATA_TAGS['discount']['class']},
            )
            .find('span')
            .text
        )
    except AttributeError:
        discount = None
    return discount


def get_description(product_soup: BeautifulSoup) -> Optional[str]:
    """Метод получения описания продукта.

    Args:
        product_soup: BeautifulSoup страницы продукта.

    Returns:
        Описание или None, если описание не найдено.
    """
    try:
        description = unicodedata.normalize(
            'NFKD',
            product_soup.find(
                DATA_TAGS['description']['tag'],
                {'class': DATA_TAGS['description']['class']},
            ).text,
        )
    except AttributeError:
        description = None
    return description


def parse_ozon_seller(url: str, products_count: int) -> HttpResponse:
    """Парсинг страницы продавца на Ozon.

    Args:
        url: адрес главной страницы.
        products_count: необходимое количество продуктов.

    Returns:
        Response с информацией об ошибках создания или статус-код 201.
    """
    request_date = datetime.now()
    driver = start_driver()
    logging.info('Драйвер запущен')
    new_ids = get_new_products(driver, url, products_count)
    logging.info(f'Выбрано новых элементов: {len(new_ids)}')
    saved_products = []
    for product_id in new_ids:
        product_html = get_html(
            driver,
            get_ozon_product_url(product_id),
            PRODUCT_PAGE_MARK,
        )
        product_soup = BeautifulSoup(product_html, 'lxml')
        serializer = ProductWriteSerializer(
            data={
                'name': get_name(product_soup),
                'image_url': get_image_url(product_soup),
                'price': get_price(product_soup),
                'discount': get_discount(product_soup),
                'description': get_description(product_soup),
                'ozon_id': product_id,
                'request_date': request_date,
            },
        )
        if not serializer.is_valid():
            message = (
                'Задача на парсинг товаров с сайта Ozon '
                'завершена преждевременно.'
                f'Товары не сохранены.'
                f'Были замечены следующие ошибки: {serializer.errors}'
            )
            sync_send_message(CHAT_ID, message)
            logging.error(message)
            return JsonResponse(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        saved_products.append(serializer)
    driver.close()
    driver.quit()
    created_products = Product.objects.bulk_create(
        [
            Product(**serializer.validated_data)
            for serializer in saved_products
        ],
    )
    message = (
        'Задача на парсинг товаров с сайта Ozon завершена. '
        f'Сохранено: {products_count} товаров.'
    )
    sync_send_message(CHAT_ID, message)
    logging.info(message)
    return JsonResponse(
        ProductReadSerializer(created_products, many=True).data,
        status=status.HTTP_201_CREATED,
        safe=False,
    )
