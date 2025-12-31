
from typing import Generic, List, Tuple, TypeVar
from statelessauth.config import StatelessAuthConfig
from statelessauth.prometheus import stateless_auth_decode_decorator, stateless_auth_encode_decorator
from statelessauth.wire import AuthWire

from jose.jws import Key
from jose import jws, JWSError

import json

T = TypeVar("T")

class AuthEngine(Generic[T]):
    # Engine Name
    __name: str = None
    @property
    def name (self):
        return self.__name
    @name.setter
    def name (self, value: str):
        self.__name = value

    __key: "Key | None" = None

    __keyname : str
    __scheme  : AuthWire[T]

    __algorithms : List[str]
    
    def __init__(self, keyname: str, scheme: AuthWire[T], algorithms: List[str] = [ "RS256" ]):
        self.__keyname = keyname
        self.__scheme  = scheme

        assert len(algorithms) != 0
        self.__algorithms = algorithms

    @property
    def key (self) -> Key:
        if self.__key is not None:
            return self.__key
        return StatelessAuthConfig.instance().get_key( self.__keyname )
    @key.setter
    def key (self, value: "Key | None"):
        self.__key = value
    @property
    def urlpatterns (self):
        return []

    def headers (self, data: T):
        return {}
    def payload_from_wired (self, wired):
        return wired
    def wired_from_payload (self, payload):
        return payload
    def validate_payload (self, payload):
        return True

    @stateless_auth_encode_decorator
    def encode (self, data: T):
        wired = self.__scheme.encode(data)
        return jws.sign(self.payload_from_wired(wired), self.key, self.headers(data), self.__algorithms[0])
    @stateless_auth_decode_decorator
    def decode (self, token, verify = True, return_payload = False):
        try:
            payload = jws.verify(token, self.key.public_key(), self.__algorithms)
            payload = json.loads(payload)

            if return_payload:
                return payload

            if not self.validate_payload( payload ):
                raise JWSError()
            
            wired = self.wired_from_payload(payload)

            return self.__scheme.decode(wired)
        except JWSError as error:
            if verify: raise error

            return None