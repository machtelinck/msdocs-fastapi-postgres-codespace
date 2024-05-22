# tests/conftest.py
import pytest
import os
import sys

# Assurez-vous que le répertoire du projet Django est dans le PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../app_django")))

os.environ['DJANGO_SETTINGS_MODULE'] = 'app_django.settings'

import django
from django.conf import settings

@pytest.fixture(scope='session')
def django_db_setup():
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
    django.setup()
