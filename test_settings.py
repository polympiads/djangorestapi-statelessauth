
from jose.backends.rsa_backend import RSAKey

from rest_framework_statelessauth.contrib.auth.views import user_acquire_view
from rest_framework_statelessauth.contrib.auth.wire import UserWire
from rest_framework_statelessauth.engine.refresh import RefreshEngine

SECRET_KEY = 'rest_framework_statelessauth'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'rest_framework_statelessauth',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
    },
}

USE_TZ = True

SIMPLE_PRIVATE_KEY = b"""-----BEGIN PRIVATE KEY-----
MIIBVgIBADANBgkqhkiG9w0BAQEFAASCAUAwggE8AgEAAkEA3psfY0ehpcheM3k5
B60iyL5uL0PGjVgNi3/KXzSRH7LzFBB9XBtToAy9ufFWcuHVcfKn+KYcEZLERbly
q5YaDwIDAQABAkEA3LNPW08ZpRQS0VXOhR3S7tReyd2YbWpvg28fZWTovVMEzP8h
Pz4FgNE2FVOlGGoxwk8dqnQ/bRDqBBxgCrJpAQIhAPSgWgcLJjRkGPbfLY2JrfHx
LT+oE1kpm6FOtlQhq7NHAiEA6PSsopNnNAqhKz/XKN8OZ1Sj/0EvLzOMIc92NiZ+
dvkCIQCoIh4+gRc9Ix9VbodspJh9lfo3qlnCCqsA74y5vnq4uQIgG2JnyNS7FQsK
1yKyEEPoVY1FmgP3n/zXREI3CzaLN0ECIQDzJclV7dkT5PY80Ol34HsHzFjg9n11
7DTSeALTluCIUg==
-----END PRIVATE KEY-----"""

SL_AUTH_KEY_BACKENDS = {
    "default": RSAKey( SIMPLE_PRIVATE_KEY, 'RS256' )
}
SL_AUTH_ENGINES = {
    "default": RefreshEngine( "default", UserWire(), user_acquire_view )
}

SL_AUTH_MIDDLEWARES = {
    "auth": {
        "engine" : "default",
        "header" : ("Authorization", "Bearer"),
        "field"  : "user"
    }
}



PASSWORD_HASHERS = [
    # MD5 Password Hashing is used to make tests run a
    # Little bit faster this is not meant to be done in
    # Production as it decreases security. 
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]
