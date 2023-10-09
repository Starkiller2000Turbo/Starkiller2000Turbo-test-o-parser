import re
import unicodedata
from http import HTTPStatus
from time import sleep
from typing import Any, List

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from django.http import HttpResponse, JsonResponse
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from api.v1.serializers import ProductSerializer
from core.constants import OZON_PRODUCT_URL
from products.models import Product


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
            WebDriverWait(driver, 100).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, css_selector),
                ),
            )
        except TimeoutException as ex:
            raise TimeoutException(f'Страница {url} не загрузилась' + str(ex))
    else:
        sleep(7)
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
    html = get_html(driver, url)
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


def get_new_elements(
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
    pages_count = count_pages(driver, url)
    new_ids = get_new_products_on_page(
        driver,
        url,
        created_ids,
    )
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
            if len(new_ids) >= products_count:
                return new_ids[:products_count]
        return new_ids


ELEMENT_TAGS = {
    'name': {'tag': 'h1', 'class': 'kz5'},
    'image': {'tag': 'div', 'class': 'lj8'},
    'price': {'tag': 'div', 'class': 'ky8'},
}


def parse_ozon_seller(url: str, products_count: int) -> HttpResponse:
    """Парсинг страницы продавца на Ozon.

    Args:
        url: адрес главной страницы.
        products_count: необходимое количество продуктов.

    Returns:
        Response с информацией об ошибках создания или статус-код 201.
    """
    driver = start_driver()
    new_ids = get_new_elements(driver, url, products_count)
    for product_id in new_ids:
        product_html = get_html(
            driver,
            get_ozon_product_url(product_id),
            'div.aby9',
        )
        product_soup = BeautifulSoup(product_html, 'lxml')
        with open('product.html', 'wb') as f:
            f.write(str(product_soup.prettify()).encode('utf-8', 'ignore'))
        name = product_soup.find('h1', {'class': 'kz5'}).text
        image = product_soup.find('div', {'class': 'jm2'}).find('img')
        image_url = image['src']
        price = ''.join(
            product_soup.find('span', {'class': 'k1z'}).text.split()[:-1],
        )
        try:
            discount = (
                product_soup.find('div', {'class': 'i2 j2 p9k'})
                .find('span')
                .text
            )
        except AttributeError:
            discount = None
        try:
            description = unicodedata.normalize(
                'NFKD',
                product_soup.find('div', {'class': 'ra-a1'}).text,
            )
        except AttributeError:
            description = None
        serializer = ProductSerializer(
            data={
                'name': name,
                'image_url': image_url,
                'price': price,
                'discount': discount,
                'description': description,
                'ozon_id': product_id,
            },
        )
        if not serializer.is_valid():
            return JsonResponse(
                serializer.errors,
                status=HTTPStatus.BAD_REQUEST,
            )
        serializer.save()
    driver.close()
    driver.quit()
    return HttpResponse(status=HTTPStatus.CREATED)
