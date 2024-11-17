
from django.test import TestCase

from rest_framework_statelessauth.config import *
from jose.backends.rsa_backend import RSAKey

from django.conf import settings

from rest_framework_statelessauth.contrib.auth.wire import UserWire

class ConfigTestCases(TestCase):
    def test_simple_auth_write (self):
        config = SAuthMiddlewareConfig()

        assert config.key    == "default"
        assert config.header == "Authorization"
        assert config.scheme is None
        assert config.urls   is None
    def test_configured_auth_write (self):
        config = SAuthMiddlewareConfig({
            "key"    : "simple",
            "header" : "Auth",
            "scheme" : "custom",
            "urls"   : [ "/" ]
        })

        assert config.key    == "simple"
        assert config.header == "Auth"
        assert config.scheme == "custom"
        assert config.urls   == [ "/" ]
    def test_default_config (self):
        assert StatelessAuthConfig() is StatelessAuthConfig.instance()

        instance = StatelessAuthConfig()

        default_key = instance.get_key("default")
        assert default_key is not None
        assert isinstance(default_key, RSAKey)
        assert not default_key.is_public()
        assert default_key is settings.SL_AUTH_KEY_BACKENDS['default']

        assert instance.get_key("custom") is None
        middlewares = instance.middlewares
        assert len(middlewares) == 1
        name, middleware = middlewares[0]
        assert name == "auth"
        assert middleware.key    == "default"
        assert middleware.header == "Authorization"
        assert isinstance(middleware.scheme, UserWire)
        assert middleware.urls   is None
    def test_custom_config (self):
        samc1 = SAuthMiddlewareConfig()
        samc2 = SAuthMiddlewareConfig({
            "key"    : "simple",
            "header" : "Auth",
            "scheme" : "custom",
            "urls"   : [ "/" ]
        })
        instance = StatelessAuthConfig.create_config({
            'nk': 'CKEY'
        }, {
            "nm" : samc1,
            'rm' : samc2
        })

        assert instance is not StatelessAuthConfig()
        assert instance is not StatelessAuthConfig.instance()

        assert instance.get_key('nk') == 'CKEY'
        assert instance.get_key('ok') is None
        assert instance.middlewares == [ ('nm', samc1), ('rm', samc2) ]