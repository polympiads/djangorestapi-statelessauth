
from typing import Dict, List, Self, Tuple, Union

from rest_framework_statelessauth.wire import AuthWire

from jose.jws import Key
from django.conf import settings

class SAuthMiddlewareConfig:
    key: str

    header: str
    scheme: AuthWire

    urls: List[str] | None

    def __init__(self, obj: Dict = {}) -> None:
        self.key    = 'default'
        self.header = 'Authorization'
        self.scheme = None
        self.urls   = None

        if 'key'    in obj: self.key    = obj['key']
        if 'header' in obj: self.header = obj['header']
        if 'scheme' in obj: self.scheme = obj['scheme']
        if 'urls'   in obj: self.urls   = obj['urls']
    @staticmethod
    def create (input):
        if isinstance(input, SAuthMiddlewareConfig): return input
        return SAuthMiddlewareConfig(input)

class StatelessAuthConfig:
    SL_AUTH_KEY_BACKENDS = "SL_AUTH_KEY_BACKENDS"
    SL_AUTH_MIDDLEWARES  = "SL_AUTH_MIDDLEWARES"

    __config: "StatelessAuthConfig | None" = None

    __key_backends : Dict[str, Key]
    __middlewares  : List[Tuple[str, SAuthMiddlewareConfig]]

    @property
    def middlewares (self):
        return self.__middlewares

    def get_key (self, name: str) -> Key:
        return self.__key_backends.get(name, None)
    def load_config (self):
        if hasattr(settings, self.SL_AUTH_KEY_BACKENDS):
            self.__key_backends = getattr(settings, self.SL_AUTH_KEY_BACKENDS)
        
        if hasattr(settings, self.SL_AUTH_MIDDLEWARES):
            middlewares: Dict = getattr(settings, self.SL_AUTH_MIDDLEWARES)
            self.__middlewares = [
                (key, SAuthMiddlewareConfig.create( middlewares[key] ))
                for key in middlewares.keys()
            ]
            self.__middlewares.sort(key = lambda key: key[0])

    def __init__(self, load_config = True) -> None:
        if load_config:
            self.load_config()

    def __new__(cls, load_config = True) -> Self:
        if cls != StatelessAuthConfig or not load_config:
            return super().__new__(cls)
        
        if StatelessAuthConfig.__config is not None:
            return StatelessAuthConfig.__config

        StatelessAuthConfig.__config = super().__new__(cls)
        return StatelessAuthConfig.__config
    @staticmethod
    def instance():
        return StatelessAuthConfig()
    @staticmethod
    def create_config (key_backends, middlewares):
        conf = StatelessAuthConfig(False)
        conf.__key_backends = key_backends
        conf.__middlewares = [
            (key, SAuthMiddlewareConfig.create(middlewares[key]))
            for key in middlewares.keys()
        ]
        conf.__middlewares.sort(key = lambda key: key[0])

        return conf