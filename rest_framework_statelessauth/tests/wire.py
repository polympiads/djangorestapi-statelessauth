
from typing import Any

from django.test import TestCase
from rest_framework_statelessauth.wire import AuthWire

class SimpleUserModel:
    username: str

    def __init__(self, username: str):
        self.username = username
    def __eq__(self, value: object) -> bool:
        return isinstance(value, SimpleUserModel) and value.username == self.username

class CustomAuthWire(AuthWire[SimpleUserModel]):
    def encode(self, value: SimpleUserModel) -> Any:
        return { 'username': value.username }
    def decode(self, value: Any) -> SimpleUserModel:
        return SimpleUserModel(value['username'])

class DefaultAuthWireTestCases(TestCase):
    def setUp(self) -> None:
        self.wire = AuthWire()
    def test_encode_throws (self):
        try:
            self.wire.encode(None)
            assert False
        except NotImplementedError:
            return
    def test_decode_throws (self):
        try:
            self.wire.decode(None)
            assert False
        except NotImplementedError:
            return
        
class CustomAuthWireTestCases(TestCase):
    def setUp(self) -> None:
        self.user1 = SimpleUserModel("user1")
        self.user2 = SimpleUserModel("user2")

        self.wire = CustomAuthWire()
    def test_initial_model (self):
        assert self.user1.username == "user1"
        assert self.user2.username == "user2"
    def test_encode_model (self):
        assert self.wire.encode(self.user1) == { 'username': 'user1' }
        assert self.wire.encode(self.user2) == { 'username': 'user2' }
    def test_equals_model (self):
        assert self.user1 == self.user1
        assert self.user2 != self.user1
    def test_decode_model (self):
        assert self.wire.decode({ 'username': 'user1' }) == self.user1
        assert self.wire.decode({ 'username': 'user2' }) == self.user2