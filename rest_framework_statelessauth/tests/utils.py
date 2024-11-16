
from typing import Any, Generic, List, Tuple, TypeVar

from rest_framework_statelessauth.wire import AuthWire


T = TypeVar("T")

class TestWire(Generic[T]):
    __wire  : AuthWire[T]
    __pairs : List[Tuple[T, Any]]
    
    def setup (self, wire: AuthWire[T], pairs: List[Tuple[T, Any]]):
        self.__wire  = wire
        self.__pairs = pairs

    def traverse_eq (self, a, b):
        if isinstance(a, list):
            return isinstance(b, list) and all([ self.traverse_eq(x, y) for x, y in zip(a, b) ]) and len(a) == len(b)
        if isinstance(a, dict):
            return isinstance(b, dict) and a.keys() == b.keys() and all([ self.traverse_eq(a[x], b[x]) for x in a.keys() ]) 
        return a == b

    def test_encode (self):
        for dec, enc in self.__pairs:
            assert self.traverse_eq( self.__wire.encode(dec), enc )
    def test_decode (self):
        for dec, enc in self.__pairs:
            assert self.__wire.decode(enc) == dec
