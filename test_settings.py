SECRET_KEY = 'rest_framework_statelessauth'

INSTALLED_APPS = (
    'rest_framework_statelessauth',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
    },
}

USE_TZ = True