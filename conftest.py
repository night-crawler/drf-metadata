import os
import pytest


@pytest.fixture(scope='session', autouse=True)
def init():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pytests.django_settings')

    import django
    django.setup()
