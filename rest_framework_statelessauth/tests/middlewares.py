
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase

from django.contrib.auth import models

from rest_framework_statelessauth.contrib.auth.models import User
from rest_framework_statelessauth.contrib.auth.views import user_acquire_view
from rest_framework_statelessauth.contrib.auth.wire import UserWire
from rest_framework_statelessauth.engine.refresh import RefreshEngine
from rest_framework_statelessauth.middlewares import AuthMiddleware
from rest_framework_statelessauth.config import StatelessAuthConfig

def home_page (request: HttpRequest):
    user: "User | None" = request.user

    username = "Anonymous"
    if user is not None:
        username = user.username

    return HttpResponse(f"Hello, {username} !")

class MiddlewareTestCases(TestCase):
    def setUp(self) -> None:
        self.home_page = AuthMiddleware( home_page )

        self.factory = RequestFactory()

        self.user = models.User.objects.create_user("user", "user@gmail.com", "user")

        self.engine1 = RefreshEngine( "default", UserWire(), user_acquire_view )

    def test_home_page_no_header (self):
        request = self.factory.get("/")

        response = self.home_page(request)

        assert response.status_code == 200
        assert response.content     == b"Hello, Anonymous !"
    def test_home_page_no_bearer (self):
        request = self.factory.get("/", headers={ "Authorization": "NoBearer A" })

        response = self.home_page(request)

        assert response.status_code == 403
    def test_home_page_signed_in (self):
        token = self.engine1.encode( User.from_user(self.user) )

        request = self.factory.get("/", headers={ "Authorization": f"Bearer {token}" })

        response = self.home_page(request)

        assert response.status_code == 200
        assert response.content     == b"Hello, user !"
    def test_home_page_signed_in_no_type (self):
        chome_page = AuthMiddleware(
            home_page,
            StatelessAuthConfig.create_config({
                "default" : self.engine1.key
            }, {
                "engine": self.engine1
            }, {
                "auth": {
                    "engine" : "default",
                    "header" : ("Authorization", ""),
                    "field"  : "user"
                }
            })
        )
        token = self.engine1.encode( User.from_user(self.user) )

        request = self.factory.get("/", headers={ "Authorization": f"{token}" })

        response = chome_page(request)

        assert response.status_code == 200
        assert response.content     == b"Hello, user !"
