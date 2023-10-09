import logging
import re
import unicodedata
from datetime import datetime
from http import HTTPStatus
from time import sleep
from typing import Any, List, Optional

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from django.http import HttpResponse
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from api.v1.serializers import ProductSerializer
from bot.bot import CHAT_ID, bot, sync_send_message
from core.constants import OZON_PRODUCT_URL
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
    driver.get(url)
    if css_selector:
        try:
            wait_delay = 8
            WebDriverWait(driver, wait_delay).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, css_selector),
                ),
            )
            logging.info(f'Страница {url} загрузилась')
            sleep_delay = 2
            sleep(sleep_delay)
        except TimeoutException as ex:
            message = f'Страница {url} не загрузилась\n' + str(ex)
            # sync_send_message(CHAT_ID, message)
            logging.error(message)
    else:
        delay = 7
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
    html = get_html(driver, url)
    pages_count = int(
        re.search(  # type: ignore[union-attr]
            r'"totalPages":(\d+)',
            html,
        )
        .group(1)
        .strip("'"),
    )
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
    html = get_html(driver, url, 'div.wi4')
    soup = BeautifulSoup(html, 'lxml')
    ozon_ids = [
        int(
            re.search(  # type: ignore[union-attr]
                r'(\d+)/',
                item.find('a')['href'],
            ).group(1),
        )
        for item in soup.find('div', {'class': 'wi4'}).find_all(
            'div',
            {'class': 'u1i ui2'},
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
    logging.info(f'Количество уже существующих товров: {len(created_ids)}')
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
                f'Количество новых элементов на странице: {len(new_ids)}'
            )
            if len(new_ids) >= products_count:
                return new_ids[:products_count]
        return new_ids


def get_name(product_soup: BeautifulSoup) -> Optional[str]:
    try:
        name = product_soup.find('h1', {'class': 'kz5'}).text
    except AttributeError as err:
        logging.info(f'Не удалось получить имя: {err}')
        name = None
    return name


def get_image_url(product_soup: BeautifulSoup) -> Optional[str]:
    try:
        image = product_soup.find('div', {'class': 'jm2'}).find('img')
        image_url = image['src']
    except AttributeError or TypeError as err:
        logging.info(f'Не удалось получить адрес картинки: {err}')
        image_url = None
    return image_url


def get_price(product_soup: BeautifulSoup) -> Optional[str]:
    try:
        price = ''.join(
            product_soup.find('span', {'class': 'k1z'}).text.split()[:-1],
        )
    except AttributeError as err:
        logging.info(f'Не удалось получить цену: {err}')
        price = None
    return price


def get_discount(product_soup: BeautifulSoup) -> Optional[str]:
    try:
        discount = (
            product_soup.find('div', {'class': 'i2 j2 p9k'}).find('span').text
        )
    except AttributeError:
        discount = None
    return discount


def get_description(product_soup: BeautifulSoup) -> Optional[str]:
    try:
        description = unicodedata.normalize(
            'NFKD',
            product_soup.find('div', {'class': 'ra-a1'}).text,
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
    logging.info(f'Количество новых элементов: {len(new_ids)}')
    saved_products = 0
    for product_id in new_ids:
        product_html = get_html(
            driver,
            get_ozon_product_url(product_id),
            'div.aby9',
        )
        product_soup = BeautifulSoup(product_html, 'lxml')
        serializer = ProductSerializer(
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
                'Задача на парсинг товаров с сайта Ozon завершена преждевременно.'
                f'Сохранены не все товары: {saved_products} товаров.'
                f'Были замечены следующие ошибки: {serializer.errors}'
            )
            sync_send_message(CHAT_ID, message)
            logging.error(bot)
            return HttpResponse(status=HTTPStatus.BAD_REQUEST)
        serializer.save()
        saved_products += 1
    driver.close()
    driver.quit()
    message = f'Задача на парсинг товаров с сайта Ozon завершена.\nСохранено: {products_count} товаров.'
    sync_send_message(CHAT_ID, message)
    logging.info(message)
    return HttpResponse(status=HTTPStatus.CREATED)
