DEBUG = True

SECRET_KEY = 'lol'

INSTALLED_APPS = [
    'pytests.test_app',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'pytests/test.sqlite',
    }
}
