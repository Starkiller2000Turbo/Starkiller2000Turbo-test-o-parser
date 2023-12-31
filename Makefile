WORKDIR = ozon_parser
MANAGE = python $(WORKDIR)/manage.py
BASE_MANAGE = python manage.py

default:
	$(MANAGE) makemigrations
	$(MANAGE) migrate
	$(MANAGE) runserver

style:
	isort $(WORKDIR)
	black -S -l 79 $(WORKDIR)
	flake8 $(WORKDIR)
	mypy $(WORKDIR)

pip:
	python -m pip install --upgrade pip

venv:
	python -m venv venv

requirements: 
	python -m pip install --upgrade pip; \
	pip install -r requirements.txt; \

project:
	django-admin startproject $(name)

app: 
	cd $(WORKDIR); \
	$(BASE_MANAGE) startapp $(name); \
	cd ..

migrations:
	$(MANAGE) makemigrations

migrate:
	$(MANAGE) migrate

superuser:
	$(MANAGE) createsuperuser

run:
	$(MANAGE) runserver

polling:
	python $(WORKDIR)/start_polling.py

celery:
	cd $(WORKDIR); \
	python -m celery -A ozon_parser worker -l info -P eventlet; \
	cd ..

redis:
	redis-server $(path)

static:
	$(MANAGE) collectstatic