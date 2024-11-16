
from typing import TYPE_CHECKING, List
    
if TYPE_CHECKING:
    import django.contrib.auth.models as dmodels

class Permission:
    name:     str
    codename: str

    def __init__(self, name: str, codename: str):
        self.name     = name
        self.codename = codename
    def __eq__(self, value: object) -> bool:
        return isinstance(value, Permission) \
           and self.name     == value.name \
           and self.codename == value.codename

    @staticmethod
    def from_permission (permission: "dmodels.Permission") -> "Permission":
        return Permission( permission.name, permission.codename )

class Group:
    name: str

    permissions: List[Permission]

    def __init__(self, name: str, permissions: List[Permission]):
        self.name = name

        self.permissions = permissions
    def __eq__(self, value: object) -> bool:
        return isinstance(value, Group) \
           and self.name == value.name \
           and all([ x in self.permissions for x in value.permissions ]) \
           and len(self.permissions) == len(value.permissions)

    @staticmethod
    def from_group (group: "dmodels.Group") -> "Group":
        dPermissions = group.permissions.all()

        permissions = [ Permission.from_permission(permission) for permission in dPermissions ]

        return Group(group.name, permissions)

class User:
    username: str

    is_anonymous     : bool
    is_authenticated : bool

    is_staff     : bool
    is_active    : bool
    is_superuser : bool

    groups: List[Group]

    def __init__(
            self,

            username : str,
            
            is_anonymous     : bool, 
            is_authenticated : bool,

            is_staff     : bool,
            is_active    : bool,
            is_superuser : bool,

            groups : List[Group]
        ) -> None:
        
        self.username = username

        self.is_anonymous     = is_anonymous
        self.is_authenticated = is_authenticated

        self.is_staff     = is_staff
        self.is_active    = is_active
        self.is_superuser = is_superuser

        self.groups = groups

    def __eq__(self, value: object) -> bool:
        return isinstance(value, User) \
           and self.username == value.username \
           and self.is_anonymous == value.is_anonymous \
           and self.is_authenticated == value.is_authenticated \
           and self.is_staff == value.is_staff \
           and self.is_active == value.is_active \
           and self.is_superuser == value.is_superuser \
           and len(self.groups) == len(value.groups) \
           and all([ x in value.groups for x in self.groups ])

    @staticmethod
    def from_user (user: "dmodels.User") -> "User":
        dGroups = user.groups.all()

        groups = [ Group.from_group(group) for group in dGroups ]

        return User(
            user.username,

            user.is_anonymous,
            user.is_authenticated,
            user.is_staff,
            user.is_active,
            user.is_superuser,

            groups
        )