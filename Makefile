ACTIVATE = . .venv/bin/activate
PYTHON = python3
SEP = &&

install:
	$(PYTHON) -m venv .venv
	$(ACTIVATE)
	pip install -r requirements.txt

run:
	$(ACTIVATE)
	$(PYTHON) manage.py runserver

migrate:
	$(ACTIVATE)
	$(PYTHON) manage.py makemigrations
	$(PYTHON) manage.py migrate

create_translations:
	$(ACTIVATE)
	$(PYTHON) manage.py makemessages -l es
	$(PYTHON) manage.py makemessages -l gl

apply_translations:
	$(ACTIVATE)
	$(PYTHON) manage.py compilemessages

clean:
ifeq ($(OS),Windows_NT)
	powershell -Command "Get-ChildItem -Path . -Recurse -Filter '__pycache__' | Remove-Item -Recurse -Force"
	powershell -Command "Get-ChildItem -Path . -Recurse -Filter '*.pyc' | Remove-Item -Force"
else
	find . -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
endif