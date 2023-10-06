WORKDIR = ozon_parser
MANAGE = python $(WORKDIR)/manage.py

default:
	$(MANAGE) makemigrations
	$(MANAGE) migrate
	$(MANAGE) runserver

style:
	isort $(WORKDIR)
	black -S -l 79 $(WORKDIR)
	flake8 $(WORKDIR)
	mypy $(WORKDIR)

app: 
	$(MANAGE) startapp $(name)

migrations:
	$(MANAGE) makemigrations

migrate:
	$(MANAGE) migrate

superuser:
	$(MANAGE) createsuperuser

run:
	$(MANAGE) runserver

pip:
	python -m pip install --upgrade pip

make env:
	pip install -r DRF-requirements.txt

project:
	django-admin startproject $(name)