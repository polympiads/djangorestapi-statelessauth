
from typing import TYPE_CHECKING, Dict, List, Self, Tuple, Union

from statelessauth.wire import AuthWire

if TYPE_CHECKING:
    from statelessauth.engine.abstract import AuthEngine

from jose.jws import Key
from django.conf import settings

class SAuthMiddlewareConfig:
    engine: str
    header: Tuple[str, str]
    field : str

    urls: List[str] | None

    def get_engine (self) -> "AuthEngine":
        return StatelessAuthConfig.instance().get_engine(self.engine)

    def __init__(self, obj: Dict = {}) -> None:
        self.engine = 'default'
        self.header = ('Authorization', 'Bearer')
        self.field  = 'unknown'
        self.urls   = None

        if 'engine' in obj:
            self.engine = obj['engine']
        if 'header' in obj:
            self.header = obj['header']
        if 'urls'   in obj:
            self.urls   = obj['urls']
        if 'field'  in obj:
            self.field  = obj['field']
    @staticmethod
    def create (input):
        if isinstance(input, SAuthMiddlewareConfig): return input
        return SAuthMiddlewareConfig(input)

class StatelessAuthConfig:
    SL_AUTH_KEY_BACKENDS = "SL_AUTH_KEY_BACKENDS"
    SL_AUTH_MIDDLEWARES  = "SL_AUTH_MIDDLEWARES"
    SL_AUTH_ENGINES      = "SL_AUTH_ENGINES"

    __config: "StatelessAuthConfig | None" = None

    __key_backends : Dict[str, Key]
    __middlewares  : List[Tuple[str, SAuthMiddlewareConfig]]
    __engines      : "Dict[str, AuthEngine]"

    @property
    def middlewares (self) -> List[Tuple[str, SAuthMiddlewareConfig]]:
        return self.__middlewares

    def get_key (self, name: str) -> "Key | None":
        return self.__key_backends.get(name, None)
    def get_engine (self, name: str) -> "AuthEngine | None":
        return self.__engines.get(name, None)
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

        if hasattr(settings, self.SL_AUTH_ENGINES):
            self.__engines = getattr(settings, self.SL_AUTH_ENGINES)

            for name in self.__engines.keys():
                engine = self.__engines[name]

                engine.name = name

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
    def create_config (key_backends, engines, middlewares):
        conf = StatelessAuthConfig(False)
        conf.__key_backends = key_backends
        conf.__engines      = engines
        conf.__middlewares  = [
            (key, SAuthMiddlewareConfig.create(middlewares[key]))
            for key in middlewares.keys()
        ]
        conf.__middlewares.sort(key = lambda key: key[0])

        return conf