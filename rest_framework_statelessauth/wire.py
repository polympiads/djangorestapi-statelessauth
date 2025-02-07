
from typing import Any, Generic, TypeVar

T = TypeVar("T")

class AuthWire(Generic[T]):
    def encode (self, value: T) -> Any:
        raise NotImplementedError()
    def decode (self, value: Any) -> T:
        raise NotImplementedError()
