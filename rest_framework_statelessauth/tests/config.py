
from django.test import TestCase

from rest_framework_statelessauth.config import *
from rest_framework_statelessauth.engine.abstract import AuthEngine
from jose.backends.rsa_backend import RSAKey

from django.conf import settings

from rest_framework_statelessauth.contrib.auth.wire import UserWire

class ConfigTestCases(TestCase):
    def test_simple_auth_write (self):
        config = SAuthMiddlewareConfig()

        assert config.engine == "default"
        assert config.header == ("Authorization", "Bearer")
        assert config.field  == "unknown"
        assert config.urls   is None
    def test_configured_auth_write (self):
        config = SAuthMiddlewareConfig({
            "engine" : "simple",
            "header" : ("Auth", "Type"),
            "field"  : "cfield",
            "urls"   : [ "/" ]
        })

        assert config.engine == "simple"
        assert config.header == ("Auth", "Type")
        assert config.field  == "cfield"
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
        assert middleware.engine == "default"
        assert middleware.header == ("Authorization", "Bearer")
        assert middleware.field  == "user"
        assert middleware.urls   is None

        assert StatelessAuthConfig().get_engine( "default" ) is settings.SL_AUTH_ENGINES['default']
        assert StatelessAuthConfig().get_engine( "_______" ) is None

        assert middleware.get_engine() is not None
        middleware = SAuthMiddlewareConfig()
        middleware.engine = "default"
        assert middleware.get_engine() is not None
        middleware.engine = "oe"
        assert middleware.get_engine() is None
    def test_custom_config (self):
        samc1 = SAuthMiddlewareConfig()
        samc2 = SAuthMiddlewareConfig({
            "engine" : "simple",
            "header" : "Auth",
            "field"  : "nfield",
            "urls"   : [ "/" ]
        })
        eng = AuthEngine( "simple", AuthWire )
        instance = StatelessAuthConfig.create_config({
            'nk': 'CKEY'
        }, {
            "ne": eng
        }, {
            "nm" : samc1,
            'rm' : samc2
        })

        assert instance is not StatelessAuthConfig()
        assert instance is not StatelessAuthConfig.instance()

        assert instance.get_key('nk') == 'CKEY'
        assert instance.get_key('ok') is None
        assert instance.get_engine('ne') is eng
        assert instance.get_engine('oe') is None
        assert instance.middlewares == [ ('nm', samc1), ('rm', samc2) ]