
from typing import Any

from django.test import TestCase
from django.contrib.auth import models
from django.contrib.contenttypes.models import ContentType
from rest_framework_statelessauth.tests.utils import TestWire
from rest_framework_statelessauth.wire import AuthWire

from rest_framework_statelessauth.contrib.auth.models import User, Group, Permission
from rest_framework_statelessauth.contrib.auth.wire   import UserWire, GroupWire, PermissionWire

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

class UREF:
    __ct: ContentType = None

    @property
    def value (self):
        if self.__ct is None:
            self.__ct = ContentType.objects.create()
        return self.__ct
    def reset (self):
        self.__ct = None
ref = UREF()

def create_permission (name: str, codename: str, ct = None) -> models.Permission:
    if ct is None:
        ct = ref.value
    return models.Permission.objects.create( name = name, codename = codename, content_type = ct )

def _create_group (self, name: str, *args):
    perms = [self.permissions[i] for i in args]
    p0 = list(map(lambda x: x[0], perms))
    p1 = list(map(lambda x: x[1], perms))
    res = (
        Group( name, p0 ),
        {
            "name": name,
            "permissions": p1
        },
        models.Group.objects.create(
            name = name
        )
    )
    res[2].permissions.set([
                self.dperms[i]
                for i in args
            ])
    return res
class AuthPermissionTests (TestCase, TestWire[Permission]):
    def setUp(self) -> None:
        ref.reset()
        self.setup(
            PermissionWire(),
            [
                ( Permission("name", "codename"), { "name": "name", "codename": "codename" } ),
                ( Permission("name1", "codename1"), { "name": "name1", "codename": "codename1" } ),
                ( Permission("name2", "codename2"), { "name": "name2", "codename": "codename2" } ),
                ( Permission("name3", "codename3"), { "name": "name3", "codename": "codename3" } ),
                ( Permission("____4", "________4"), { "name": "____4", "codename": "________4" } )
            ]
        )
    def test_create_from_permission (self):
        for __name, __codename in [ ("name", "codename"), ("a", "b") ]:
            permission = create_permission( __name, __codename )
            
            permission = Permission.from_permission(permission)
            assert permission == Permission( __name, __codename )

class AuthGroupTests (TestCase, TestWire[Group]):
    def setUp(self) -> None:
        ref.reset()
        self.permissions = [
            ( Permission("name", "codename"), { "name": "name", "codename": "codename" } ),
            ( Permission("name1", "codename1"), { "name": "name1", "codename": "codename1" } ),
            ( Permission("name2", "codename2"), { "name": "name2", "codename": "codename2" } ),
            ( Permission("name3", "codename3"), { "name": "name3", "codename": "codename3" } ),
            ( Permission("____4", "________4"), { "name": "____4", "codename": "________4" } )
        ]
        self.dperms = [
            create_permission( value['name'], value['codename'] )
            for _, value in self.permissions
        ]

        self.groups = [
            _create_group(self, "egroup"),
            _create_group(self, "singleton", 0),
            _create_group(self, "singleton2", 2),
            _create_group(self, "full", 0, 1, 2, 3, 4),
            _create_group(self, "even", 0, 2, 4)
        ]

        class PWP(AuthWire[Permission]):
            def encode(self, value: Permission) -> Any:
                return PermissionWire().encode(value)
            def decode(self, value: Any) -> Permission:
                return PermissionWire().decode(value)

        self.setup(GroupWire(PWP), list(map(lambda e: e[:2], self.groups)))
    def test_from_group (self):
        for _a, _b, _c in self.groups:
            assert Group.from_group( _c ) == _a

class AuthUserTests (TestCase, TestWire[User]):
    def setUp(self) -> None:
        ref.reset()
        self.permissions = [
            ( Permission("name", "codename"), { "name": "name", "codename": "codename" } ),
            ( Permission("name1", "codename1"), { "name": "name1", "codename": "codename1" } ),
            ( Permission("name2", "codename2"), { "name": "name2", "codename": "codename2" } ),
            ( Permission("name3", "codename3"), { "name": "name3", "codename": "codename3" } ),
            ( Permission("____4", "________4"), { "name": "____4", "codename": "________4" } )
        ]
        self.dperms = [
            create_permission( value['name'], value['codename'] )
            for _, value in self.permissions
        ]

        self.groups = [
            _create_group(self, "egroup"),
            _create_group(self, "singleton", 0),
            _create_group(self, "singleton2", 2),
            _create_group(self, "full", 0, 1, 2, 3, 4),
            _create_group(self, "even", 0, 2, 4)
        ]

        fields = [ "username", "is_anonymous", "is_authenticated", "is_staff", "is_active", "is_superuser" ]
        def __create_user (udata, *group_ids):
            kwargs = {}
            for field, data in zip(fields, udata):
                kwargs[field] = data
            groups = [ self.groups[i] for i in group_ids ]
            g0 = list(map(lambda x: x[0], groups))
            g1 = list(map(lambda x: x[1], groups))
            g2 = list(map(lambda x: x[2], groups))

            assert udata[1] ^ udata[2]

            res = (
                User( *udata, g0 ),
                { **kwargs, "groups": g1 },
                g2
            )
            return res

        self.users = [
            __create_user( ("", True, False, False, False, False) ),
            __create_user( ("user1", False, True, False, True, False), 0 ),
            __create_user( ("userE", False, True, True, False, True), 0, 2, 4 ),
            __create_user( ("userF", False, True, True, False, True), 0, 1, 2, 3, 4 )
        ]

        class GWP(AuthWire[Group]):
            def encode(self, value: Group) -> Any:
                return GroupWire().encode(value)
            def decode(self, value: Any) -> Group:
                return GroupWire().decode(value)

        self.setup(UserWire(GWP), list(map(lambda e : e[:2], self.users)))
    def test_from_user (self):
        user = models.User.objects.create(
            username = "userE"
        )
        user.is_staff = True
        user.is_active = False
        user.is_superuser = True
        user.groups.set( self.users[2][2] )
        user.save()

        assert User.from_user(user) == self.users[2][0]