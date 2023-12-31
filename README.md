### Проект Ozon-parser

### Описание:

Парсер товаров сайта Ozon с оповещением.

В рамках данного проекта разработано Django приложение с REST API на основе Django Rest Framework (DRF) для парсинга информации о товарах магазина по ссылке https://www.ozon.ru/seller/1/products/ с сайта Ozon с помощью библиотек BeautifulSoup и Selenium.
Полученные данные сохраняются в базу данных MySQL. Информация о товарах отображается в административной панели, которая, в свою очередь, кастомизирована с использованием AdminLTE для современного и привлекательного внешнего вида приложения.

Также:
 • Парсер реализован на основании Celery-задач. 
 • Настроено оповещения о завершении парсинга через Telegram-бот.
 • Создано документирование API с помощью библиотеки Django drf-yasg.


### Как запустить проект:

Клонируйте репозиторий:
```
git clone git@github.com:Starkiller2000Turbo/Starkiller2000Turbo-test-o-parser.git
```

Измените свою текущую рабочую дерикторию:
```
cd Starkiller2000Turbo-test-o-parser
```

Создайте и активируйте виртуальное окружение

```
make venv
```
```
source venv/Scripts/activate
```

Обновите pip и установите зависимости из requirements.txt:
```
make requirements
```
Для работы приложения необходим файл .env:

```
touch .env
```

Необходимо заполнить файл .env следующим обазом:

```
SECRET_KEY=  
Секретный ключ для работы django.

DEBUG=
True/False в зависимости от необходимости режима отладки.

ALLOWED_HOSTS= 
Допустимые хосты, на которых будет работать приложение через пробел. 
Для локальной работы приложения - localhost и 127.0.0.1, для работы на сервере - также доменное имя и ip адрес.

TOKEN=
Токен Telegram-бота

CHAT_ID=
Telegram-id на которое будут отправляться сообщения

DB_NAME=
Имя базы данных MySQL

DB_USER=
Пользователь базы данных MySQL

DB_PASSWORD=
Пароль от базы данных MySQL

DB_HOST=
Хост базы данных MySQL

DB_PORT=3306
Порт базы данных MySQL

EMAIL = 
Контактный email (для документации)
```

Сохраните статику:
```
make static
```

Создайте миграции и запустите сервер:

```
make
```
Таким образом можно получить доступ к Админ-зоне.
Чтобы была возможность запустить парсинг, необходимо в отдельном окре терминала активировать Redis:
```
make redis path=path/to/redis.conf
```
В третьем окне необходимо активировать Celery:
```
make celery
```

### Как начать парсинг сайта https://www.ozon.ru/seller/1/products/:
Сделайте POST запрос на эндпоинт "products/". Укажите параметр products_count - количество товаров, данные о которых необходимо сохранить (по умолчанию - 10). 


### Эндпоинты:

| Эндпоинт              |Тип запроса| Тело запроса          |Параметры запроса                            |Ответ                                  |
|-----------------------|-----------|-----------------------|---------------------------------------------|---------------------------------------|
|/products/             |POST       |--пусто--              |products_count - количество продуктов [0..50]|Код 200                                |
|/products/             |GET        |--пусто--              |--пусто--                                    | Список всех товаров                   |
|/products/{product_id} |GET        |--пусто--              |--пусто--                                    | Информация о товаре с id product_id   |


### Авторы:

- :white_check_mark: [Starkiller2000Turbo](https://github.com/Starkiller2000Turbo)

### Стек технологий использованный в проекте:

- Python
- Django
- Django REST Framework
- API
- JSON
- Celery
- Redis
- Telegram-bot
- Logging
- Selenium
- BeautifulSoup
- MySQL
