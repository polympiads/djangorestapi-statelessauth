
from typing import TYPE_CHECKING, Any, Callable

from statelessauth.contrib.auth.models import Group, Permission, User
from statelessauth.wire import AuthWire

class PermissionWire(AuthWire[Permission]):
    def encode(self, permission: Permission) -> Any:
        return { "name": permission.name, "codename": permission.codename }
    def decode(self, value: Any) -> Permission:
        return Permission(
            value['name'],
            value['codename']
        )

class GroupWire (AuthWire[Group]):
    def __init__(self, permWireClass: Callable[[], AuthWire[Permission]] = PermissionWire):
        self.permWire = permWireClass()
    def encode(self, group: Group) -> Any:
        return {
            "name": group.name,
            "permissions": [
                self.permWire.encode(permission)
                for permission in group.permissions
            ]
        }
    def decode(self, value: Any) -> Group:
        name = value['name']

        encodedPermissions = value['permissions']
        decodedPermissions = [ self.permWire.decode(encoded) for encoded in encodedPermissions ]

        return Group(name, decodedPermissions)

class UserWire (AuthWire[User]):
    def __init__(self, groupWireClass: Callable[[], AuthWire[Group]] = GroupWire):
        self.groupWire = groupWireClass()
    def encode(self, value: User) -> Any:
        return {
            "username": value.username,

            "is_anonymous"     : value.is_anonymous,
            "is_authenticated" : value.is_authenticated,

            "is_staff"     : value.is_staff,
            "is_active"    : value.is_active,
            "is_superuser" : value.is_superuser,

            "groups": [
                self.groupWire.encode(group)
                for group in value.groups
            ]
        }
    def decode(self, value: Any) -> User:
        username = value['username']

        is_anonymous     = value['is_anonymous']
        is_authenticated = value['is_authenticated']

        is_staff     = value['is_staff']
        is_active    = value['is_active']
        is_superuser = value['is_superuser']

        groups = [
            self.groupWire.decode(encodedGroup)
            for encodedGroup in value['groups']
        ]
        return User(username, is_anonymous, is_authenticated, is_staff, is_active, is_superuser, groups)