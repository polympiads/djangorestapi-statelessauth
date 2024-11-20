
import json
import time
from django.http import HttpRequest, JsonResponse
from django.test import Client, RequestFactory, TestCase, override_settings

from django.contrib.auth.models import AnonymousUser, User
from django.urls import include, path

from rest_framework_statelessauth.contrib.auth.models import Group, Permission, User
from rest_framework_statelessauth.contrib.auth.views import user_acquire_view
from rest_framework_statelessauth.contrib.auth.wire import PermissionWire, UserWire
from rest_framework_statelessauth.engine.abstract import AuthEngine
from rest_framework_statelessauth.engine.acquire  import AcquireEngine
from rest_framework_statelessauth.engine.refresh  import RefreshEngine

from jose.backends.rsa_backend import RSAKey
from django.conf import settings
from jose import jws, JWSError

import django.contrib.auth.models as dmodels

SAMPLE_CUSTOM_KEY = b"""-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC95O3tR95Il7Sv
S5W0cmmpUFnufDWFlboRGR0U+Hjp3T2LCU/KjBlztx9hLat2gVjyJHM3uVpCwp2L
FEGdAsUh8XrdllXTOQI9/UttTFxHW0nyClIS2AnMCsyDHgYtOjXmQhnsOWmN/u1o
vYX4XjHyJucw8W0Mep31rH5Fx1918OCJrHWei/w7UbZyF2cVReQnZ1gIbH/EPjjt
TcM/qfL3DUGpsvhtlnGNhCsBQ0sD0gkiKbFlMG1JekD3hAClsELOBrPb9stDFRd6
0t9t8joGZ7uGolGYKJALLQvcyNhgFdus9sCxAOlxkJTLDkFkrGhqH2DGKjyNN2X2
LSi4VQy7AgMBAAECggEAAlPiDryIyamtD1EFNBcK8IZe89YV7zNB+p+s2ZWfdc5p
HgvZLInBw3IFMnMVh6MCQhrsRqHrrKcnYzhhAtmxLOoBhYx9iinyuxZ1wZCOuQPc
yNi+NM5CddEpZ0S2SAD5/tPkmXQCtTjgvsiZRyLFyKAYHrjMNhDytWY4jgZpnHp3
+LAOrsGGu+u1SdyI6aYWFUpN5zup09M5GXJk7TkYlKM0/QF6ZF3CoB/oROPUM/ar
eX+NZ2DUI2CURSfF+W77vdWlaQq3kpvWo2g3Bs6C38t4IF6djVx01i50M4UyLhLs
WrZNTp0rzDBYvLxltyN9ZLZ3ZBh1uE5masA7C1hTYQKBgQDxZT/o1NFZzL1q82fl
VFbMYBdELRZQK30HPd9t7cj33Fj2RSezzHjIxSH+H4X8ht5desQKfUzS15GeJM89
Y4F3Puln+MRvWF8lRLACXVed8ZeQXto75xUjHyrgJbJpOCBJNDpx/7BF1ScFctj0
z8uxiOdSQBLBXN56UMpdBpz/aQKBgQDJYgZZwPO7rVKwHrce6CGHTNG3KhSgW3KB
kJMuI47Tdh/pmUuDWeWujjcipIXvKj5rOoJB6KovF9CHgHmN+W7K351uTBsBoPdo
XFFAYKG44HEEVCjGB/bk9ttiHDFMVbV9IWw1VPXK58kUNF4oZprcoYd6sXqKdBR+
gXz995pKgwKBgGRCvWyjF+DIXNQTDM//W52/O2qhn2bk6SUc2bP600G/T2PaDUds
Ya5h0mCOD0R3b9w7pTkGGeZoip64gyroLVmt05vPgycL+VitUr1or392XJEmFFZV
AD56L4Cxp4x0N1SwUKYQoNIgWfi1Xs8vj1bJmepbmm6dd/otnB9PI94hAoGBAKyB
LqV1tpM+rkU1mnF8MTRgJoj7H/4ZN6Yq/RiZ1v/nAQEuklPrDueO5UXknuI3Uo6x
6OCieB2tDbD06asnTrO0B3xy7vNfOm+IHQXDgOUIRWeK2/5+1gxeNaD+O3CDPtr4
ZWPt6jqsgD+xeDKtadyy9YWxQCIXu3J+Y1592goXAoGAK6emoiNvVJWA/0ln766g
wsLfbaZwIxblzRkI1hbt92KqtEoE4VOCiBpwaYwMiTerGsp8nxKpEFD16m1tArDp
IY/sHSSzRETm9IH2Kj1rfhz3JEB631ax6Y8ZtsnLIwFz545lD1m19RffJJBrLp4p
vetZq+IqojCVsyPtRISfngQ=
-----END PRIVATE KEY-----"""

class AbstractEngineTestCases (TestCase):
    def setUp(self) -> None:
        self.dkey = RSAKey(settings.SIMPLE_PRIVATE_KEY, "RS256")
        self.nkey = RSAKey(SAMPLE_CUSTOM_KEY, "RS256")

        self.engine1 = AuthEngine("default", PermissionWire())
        self.engine2 = AuthEngine("default", PermissionWire(), [ "HS256", "RS256" ])
        self.engine3 = AuthEngine("nokey",   PermissionWire(), [ "HS256", "RS256" ])
        self.engine3.key = self.nkey

        return super().setUp()
    def test_default_encode (self):
        permission = Permission( "p1", "c1" )
        assert self.engine1.key.to_dict() == self.dkey.to_dict()

        encoded = self.engine1.encode( permission )
        payload = PermissionWire().encode(permission)
        expects = jws.sign( payload, self.dkey, {}, "RS256" )
        assert expects == encoded
    def test_encode_uses_first_in_algos (self):
        permission = Permission( "p1", "c1" )
        assert self.engine2.key.to_dict() == self.dkey.to_dict()

        encoded = self.engine2.encode( permission )
        payload = PermissionWire().encode(permission)
        expects = jws.sign( payload, self.dkey, {}, "HS256" )
        assert expects == encoded
    def test_encode_uses_set_key (self):
        permission = Permission( "p1", "c1" )
        assert self.engine3.key is self.nkey

        encoded = self.engine3.encode( permission )
        payload = PermissionWire().encode(permission)
        expects = jws.sign( payload, self.nkey, {}, "HS256" )
        assert expects == encoded
    def test_encode_decode_in_one_second (self):
        user = User( "user1", False, True, False, True, False, [
            Group( "group1", [
                Permission("perm1", "perm1"),
                Permission("access.log", "access.log")
            ] )
        ] )

        engine = AuthEngine( "default", UserWire(), [ "RS256" ] )
        total = 0
        for _ in range(100):
            start = time.time()
            payload = engine.encode(user)
            engine.decode(payload)
            end = time.time()

            total += end - start
        assert total <= 1
    def test_decode (self):
        for engine in [self.engine1, self.engine2, self.engine3]:
            permission = Permission( "p1", "c1" )
            
            encoded = engine.encode(permission)
            decoded = engine.decode(encoded)
            assert permission == decoded
    def test_decode_compatible (self):
        permission = Permission( "p1", "c1" )

        encoded = self.engine1.encode( permission )
        decoded = self.engine2.decode( encoded )

        assert decoded == permission
    def test_decode_incompatible_wrong_algorithm (self):
        permission = Permission( "p1", "c1" )

        encoded = self.engine2.encode( permission )
        try:
            decoded = self.engine1.decode( encoded )
            assert False
        except JWSError:
            return
    def test_decode_incompatible_wrong_key (self):
        permission = Permission( "p1", "c1" )

        encoded = self.engine1.encode( permission )
        try:
            decoded = self.engine3.decode( encoded )
            assert False
        except JWSError:
            pass
        
        decoded = self.engine3.decode( encoded, False )
        assert decoded is None
    def test_decode_incompatible_wrong_sign (self):
        permission = Permission( "p1", "c1" )

        encoded = self.engine1.encode( permission )
        try:
            decoded = self.engine3.decode( encoded + "a" )
            assert False
        except JWSError:
            return
    def test_urlpatterns (self):
        assert self.engine1.urlpatterns == []
        assert self.engine2.urlpatterns == []
        assert self.engine3.urlpatterns == []

acquire_engine = AcquireEngine( "default", UserWire(), user_acquire_view )
refresh_engine = RefreshEngine( "default", UserWire(), user_acquire_view, 0.1, 0.2 )

urlpatterns = [
    path('user/', include( acquire_engine.urlpatterns )),
    path('refr/', include( RefreshEngine( "default", UserWire(), user_acquire_view ).urlpatterns ))
]

class AcquireEngineTestCases (TestCase):
    def setUp(self) -> None:
        self.engine   = acquire_engine
        self.d_engine = AuthEngine   ( "default", UserWire() )
        self.factory  = RequestFactory()
    def test_anonymous_request (self):
        request = self.factory.get("/api/v1/.../acquire/")
        request.user = AnonymousUser()

        response = self.engine.acquire_view( request )
        assert isinstance(response, JsonResponse)
        assert response.status_code == 401
        assert response.content     == b'{"valid": false, "token": ""}'
    def test_simple_user_request (self):
        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        request = self.factory.get("/api/v1/.../acquire/?username=user&password=somepassword")
        request.user = user

        response = self.engine.acquire_view( request )
        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        token   = self.d_engine.encode( User.from_user( user ) )
        payload = {
            "valid": True,
            "token": token
        }
        assert response.content == bytes( json.dumps(payload), "utf-8" )
    @override_settings(ROOT_URLCONF="rest_framework_statelessauth.tests.engine")
    def test_with_url_dispatch_login (self):
        client = Client()
        user   = dmodels.User.objects.create_user( "user", "user@gmail.com", "user" )

        response = client.get("/user/acquire/?username=user&password=user")
        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        token   = self.d_engine.encode( User.from_user( user ) )
        payload = {
            "valid": True,
            "token": token
        }
        assert response.content == bytes( json.dumps(payload), "utf-8" )
    @override_settings(ROOT_URLCONF="rest_framework_statelessauth.tests.engine")
    def test_with_url_dispatch_logout (self):
        client = Client()

        response = client.get("/user/acquire/")
        assert isinstance(response, JsonResponse)
        assert response.status_code == 401

        payload = {
            "valid": False,
            "token": ""
        }
        assert response.content == bytes( json.dumps(payload), "utf-8" )

class RefreshEngineTestCases (TestCase):
    def setUp(self) -> None:
        self.engine   = refresh_engine
        self.d_engine = AuthEngine ( "default", UserWire() )
        self.factory  = RequestFactory()
    def test_payload_from_wired (self):
        wired = []
        ctime = time.time_ns()

        payload = self.engine.payload_from_wired( wired )

        assert payload['wired'] == wired
        assert ctime +  99_900_000 <= payload['alt'] <= ctime + 100_100_000
        assert ctime + 199_900_000 <= payload['rlt'] <= ctime + 200_100_000
    def test_wired_from_payload (self):
        wired = { "res": "some wired data", "a" : [ "b", "c" ] }
        
        payload = self.engine.payload_from_wired( wired )

        assert self.engine.wired_from_payload( payload ) == wired
    def test_payload_from_wired (self):
        wired = UserWire().encode( User( "user", True, False, False, False, False, [] ) )
        ctime = time.time_ns()

        payload = self.engine.payload_from_wired( wired )
        encoded = self.engine.encode( UserWire().decode( wired ) )

        while time.time_ns() - ctime <= 300_000_000:
            delta   =  95_000_000
            epsilon = 105_000_000

            if not (delta <= time.time_ns() - ctime <= epsilon):
                assert self.engine.validate_payload(payload) == (epsilon > time.time_ns() - ctime)
                assert (self.engine.decode( encoded, False ) is not None) == (epsilon > time.time_ns() - ctime)

            time.sleep(0.001)
    
    def test_acquire_logout (self):
        request = self.factory.get("/api/v1/.../acquire/")
        request.user = AnonymousUser()

        response = self.engine.acquire_view( request )
        assert isinstance(response, JsonResponse)
        assert response.status_code == 401
        assert response.content     == b'{"valid": false, "token": ""}'
    def test_acquire_login (self):
        engine = RefreshEngine( "default", UserWire(), user_acquire_view )

        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        request = self.factory.get("/api/v1/.../acquire/?username=user&password=somepassword")

        response = engine.acquire_view( request )
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]

        payload = jws.verify( token, engine.key.public_key(), engine._AuthEngine__algorithms )
        payload = json.loads( payload )

        assert ctime + int(1e9) * 297                  <= payload['alt'] <= ctime + int(1e9) * 303
        assert ctime + int(1e9) * (3600 * 24 * 14 - 3) <= payload['rlt'] <= ctime + int(1e9) * (3600 * 24 * 14 + 3)
    def test_refresh_without_header (self):
        request = self.factory.get("/api/v1/.../refresh/")

        response = self.engine.refresh_view( request )
        assert isinstance(response, JsonResponse)
        assert response.status_code == 400
        assert response.content     == b'{"valid": false, "token": ""}'
    def test_refresh_wrong_token (self):
        engine = RefreshEngine( "default", UserWire(), user_acquire_view )

        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        request = self.factory.get("/api/v1/.../acquire/?username=user&password=somepassword")

        response = self.engine.acquire_view( request )
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]
       
        request = self.factory.get("/api/v1/.../refresh/", headers = { "Refresh" : token + 'a' })

        response = self.engine.refresh_view( request )
        assert isinstance(response, JsonResponse)
        assert response.status_code == 401
        assert response.content     == b'{"valid": false, "token": ""}'
    def test_refresh_passed_deadline (self):
        engine = RefreshEngine( "default", UserWire(), user_acquire_view )

        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        request = self.factory.get("/api/v1/.../acquire/?username=user&password=somepassword")

        response = self.engine.acquire_view( request )
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]
        time.sleep(0.2)
        
        request = self.factory.get("/api/v1/.../refresh/", headers = { "Refresh" : token })

        response = self.engine.refresh_view( request )
        assert isinstance(response, JsonResponse)
        assert response.status_code == 401
        assert response.content     == b'{"valid": false, "token": ""}'
    def test_refresh_deadline_fine (self):
        engine = RefreshEngine( "default", UserWire(), user_acquire_view )
        engine2 = RefreshEngine( "default", UserWire(), user_acquire_view, 60 )

        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        request = self.factory.get("/api/v1/.../acquire/?username=user&password=somepassword")

        response = engine.acquire_view( request )
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]
        time.sleep(0.1)
        
        request = self.factory.get("/api/v1/.../refresh/", headers = { "Refresh" : token })

        response = engine2.refresh_view( request )
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]

        payload = jws.verify( token, engine.key.public_key(), engine._AuthEngine__algorithms )
        payload = json.loads( payload )

        assert ctime + int(1e9) * 57                   <= payload['alt'] <= ctime + int(1e9) * 63
        assert ctime + int(1e9) * (3600 * 24 * 14 - 3) <= payload['rlt'] <= ctime + int(1e9) * (3600 * 24 * 14 + 3)
    
    @override_settings(ROOT_URLCONF="rest_framework_statelessauth.tests.engine")
    def test_with_url_dispatch_logout (self):
        client = Client()

        response = client.get("/refr/acquire/")
        assert isinstance(response, JsonResponse)
        assert response.status_code == 401
        assert response.content     == b'{"valid": false, "token": ""}'
    @override_settings(ROOT_URLCONF="rest_framework_statelessauth.tests.engine")
    def test_with_url_dispatch_wrong_password (self):
        client = Client()
        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        response = client.get("/refr/acquire/?username=user&password=somewrongpassword")
        assert isinstance(response, JsonResponse)
        assert response.status_code == 401
        assert response.content     == b'{"valid": false, "token": ""}'
    @override_settings(ROOT_URLCONF="rest_framework_statelessauth.tests.engine")
    def test_with_url_dispatch_login (self):
        client = Client()
        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        response = client.get("/refr/acquire/?username=user&password=somepassword")
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]

        payload = jws.verify( token, self.engine.key.public_key(), self.engine._AuthEngine__algorithms )
        payload = json.loads( payload )

        assert ctime + int(1e9) * 297                  <= payload['alt'] <= ctime + int(1e9) * 303
        assert ctime + int(1e9) * (3600 * 24 * 14 - 3) <= payload['rlt'] <= ctime + int(1e9) * (3600 * 24 * 14 + 3)
    @override_settings(ROOT_URLCONF="rest_framework_statelessauth.tests.engine")
    def test_with_url_dispatch_deadline_passed (self):
        engine = RefreshEngine( "default", UserWire(), user_acquire_view, 0, 0 )

        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        request = self.factory.get("/api/v1/.../acquire/?username=user&password=somepassword")

        response = engine.acquire_view( request )
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]
        
        response = Client().get("/refr/refresh/", headers = { "Refresh" : token })

        assert isinstance(response, JsonResponse)
        assert response.status_code == 401
        assert response.content     == b'{"valid": false, "token": ""}'
    @override_settings(ROOT_URLCONF="rest_framework_statelessauth.tests.engine")
    def test_with_url_dispatch_no_header (self):
        engine = RefreshEngine( "default", UserWire(), user_acquire_view, 0, 0 )

        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        request = self.factory.get("/api/v1/.../acquire/?username=user&password=somepassword")

        response = self.engine.acquire_view( request )
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]
        
        response = Client().get("/refr/refresh/", headers = {})

        assert isinstance(response, JsonResponse)
        assert response.status_code == 400
        assert response.content     == b'{"valid": false, "token": ""}'
    @override_settings(ROOT_URLCONF="rest_framework_statelessauth.tests.engine")
    def test_with_url_dispatch_deadline_fine (self):
        engine2 = RefreshEngine( "default", UserWire(), user_acquire_view, 60 )

        user = dmodels.User.objects.create_user("user", "user@user.com", "somepassword")

        request = self.factory.get("/api/v1/.../acquire/?username=user&password=somepassword")

        response = engine2.acquire_view( request )
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]
        time.sleep(0.1)
        
        response = Client().get("/refr/refresh/", headers = { "Refresh" : token })
        ctime = time.time_ns()

        assert isinstance(response, JsonResponse)
        assert response.status_code == 200

        payload = json.loads( response.content )
        assert payload["valid"]
        token = payload["token"]

        payload = jws.verify( token, self.engine.key.public_key(), self.engine._AuthEngine__algorithms )
        payload = json.loads( payload )

        assert ctime + int(1e9) * 297                  <= payload['alt'] <= ctime + int(1e9) * 303
        assert ctime + int(1e9) * (3600 * 24 * 14 - 3) <= payload['rlt'] <= ctime + int(1e9) * (3600 * 24 * 14 + 3)
    