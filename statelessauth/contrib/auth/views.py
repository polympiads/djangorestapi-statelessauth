
from django.http import HttpRequest
from statelessauth.contrib.auth.models import User

def user_acquire_view (request: HttpRequest) -> "User | None":
    import django.contrib.auth.models as dmodels

    username = request.GET.get("username")
    password = request.GET.get("password")
    if username is None or password is None: return None
    
    users = list( dmodels.User.objects.filter( username = username ) )
    if len(users) == 0: return None
    user = users[0]

    if not user.check_password(password):
        return None

    return User.from_user(user)
