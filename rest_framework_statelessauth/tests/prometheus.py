
from typing import List
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import include, path
from prometheus_client import REGISTRY

from django_prometheus.conf import PROMETHEUS_LATENCY_BUCKETS
from django.contrib.auth import models

from rest_framework_statelessauth.contrib.auth.models import User
from rest_framework_statelessauth.contrib.auth.views import user_acquire_view
from rest_framework_statelessauth.contrib.auth.wire import UserWire
from rest_framework_statelessauth.engine.acquire import AcquireEngine
from rest_framework_statelessauth.engine.refresh import RefreshEngine
from rest_framework_statelessauth.prometheus import clear_metrics
from rest_framework_statelessauth.tests.middlewares import home_page
from rest_framework_statelessauth.config import StatelessAuthConfig

urlpatterns = [
    path('account/', include(StatelessAuthConfig.instance().get_engine("default").urlpatterns)),
    path('', home_page),
    path('prometheus/', include('django_prometheus.urls'))
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'rest_framework_statelessauth.middlewares.AuthMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware'
]

def loverride_settings (f):
    return override_settings(ROOT_URLCONF="rest_framework_statelessauth.tests.prometheus", MIDDLEWARE=MIDDLEWARE)(f)

BUCKETS = (
    "0.01",
    "0.025",
    "0.05",
    "0.075",
    "0.1",
    "0.25",
    "0.5",
    "0.75",
    "1.0",
    "2.5",
    "5.0",
    "7.5",
    "10.0",
    "25.0",
    "50.0",
    "75.0",
    "+Inf"
)

class _Vector:
    def __init__(self, values: List[float]):
        self.values = values
        for i in range(len(values)):
            if values[i] is None:
                values[i] = 0
        assert all([ 0 <= a <= b for a, b in zip(values, values[1:]) ])
    def less_or_equal (self, other: "_Vector"):
        return all([ a <= b for a, b in zip(self.values, other.values) ])
    def greater_or_equal (self, other: "_Vector"):
        return all([ a >= b for a, b in zip(self.values, other.values) ]) and self.values[-1] == other.values[-1]
    def add (self, other: "_Vector"):
        return _Vector( [ a + b for a, b in zip(self.values, other.values) ] )

class PrometheusMetricsTest(TestCase):
    def setUp(self) -> None:
        clear_metrics()
        
        self.client = Client()
        self.user = models.User.objects.create_user("user", "user@gmail.com", "user")
        self.engine1 = RefreshEngine( "default", UserWire(), user_acquire_view )
        self.engine1.name = "engine1"
        self.engine2 = AcquireEngine( "default", UserWire(), user_acquire_view )
        self.engine2.name = "engine2"
        self.engine3 = RefreshEngine( "default", UserWire(), user_acquire_view, 0, 0 )
        self.engine3.name = "engine3"
    @property
    def token (self):
        if not hasattr(self, "_token"):
            self._token = self.engine1.encode( User.from_user(self.user) )
        return self._token
    def get_metric (self, name: str, **kwargs):
        result = REGISTRY.get_sample_value(name, None if len(kwargs.keys()) == 0 else kwargs)
        return result
    def get_bucket_metric (self, name: str, **kwargs):
        return _Vector([ self.get_metric(name, le=bsize, **kwargs) for bsize in BUCKETS ])
    def get_metric_of_latency (self, val: float):
        return _Vector([ 1 if val <= bsize else 0 for bsize in PROMETHEUS_LATENCY_BUCKETS ])
    @loverride_settings
    def test_middleware_run_count (self):
        assert self.get_metric("stateless_auth_middleware_run_total") == 0
        self.client.get("/")
        assert self.get_metric("stateless_auth_middleware_run_total") == 1
        self.client.get("/")
        assert self.get_metric("stateless_auth_middleware_run_total") == 2
    @loverride_settings
    def test_reset_between_tests (self):
        assert self.get_metric("stateless_auth_middleware_run_total") == 0
        self.client.get("/")
        assert self.get_metric("stateless_auth_middleware_run_total") == 1
    @loverride_settings
    def test_middleware_run_latency (self):
        assert self.get_bucket_metric( "stateless_auth_middleware_run_latency_bucket" ).greater_or_equal( _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS)) )
        self.client.get("/")
        assert self.get_bucket_metric( "stateless_auth_middleware_run_latency_bucket" ).greater_or_equal( self.get_metric_of_latency(0.1) )
    @loverride_settings
    def test_middleware_run_count_per_config (self):
        assert self.get_metric("stateless_auth_middleware_run_per_config_total", middleware="auth") is None
        self.client.get("/")
        assert self.get_metric("stateless_auth_middleware_run_per_config_total", middleware="auth") == 1
        self.client.get("/")
        assert self.get_metric("stateless_auth_middleware_run_per_config_total", middleware="auth") == 2
    @loverride_settings
    def test_middleware_run_latency_per_config (self):
        assert self.get_bucket_metric("stateless_auth_middleware_run_latency_per_config_bucket", middleware="auth") \
            .greater_or_equal( _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS)) )
        self.client.get("/")
        assert self.get_bucket_metric("stateless_auth_middleware_run_latency_per_config_bucket", middleware="auth") \
            .greater_or_equal( self.get_metric_of_latency(0.1) )
    @loverride_settings
    def test_middleware_missing_per_config (self):
        target = "stateless_auth_middleware_run_per_config_missing_total"
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/")
        assert self.get_metric(target, middleware="auth") == 1
        self.client.get("/", headers = { "Authorization": "HHH" })
        assert self.get_metric(target, middleware="auth") == 1
        self.client.get("/", headers = { "Authorization": "Bearer HHH" })
        assert self.get_metric(target, middleware="auth") == 1
        self.client.get("/", headers = { "Authorization": f"Bearer {self.token}" })
        assert self.get_metric(target, middleware="auth") == 1
    @loverride_settings
    def test_middleware_valid_per_config (self):
        target = "stateless_auth_middleware_run_per_config_valid_total"
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/")
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/", headers = { "Authorization": "HHH" })
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/", headers = { "Authorization": "Bearer HHH" })
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/", headers = { "Authorization": f"Bearer {self.token}" })
        assert self.get_metric(target, middleware="auth") == 1
    @loverride_settings
    def test_middleware_no_type_per_config (self):
        target = "stateless_auth_middleware_run_per_config_no_type_total"
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/")
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/", headers = { "Authorization": "HHH" })
        assert self.get_metric(target, middleware="auth") == 1
        self.client.get("/", headers = { "Authorization": "Bearer HHH" })
        assert self.get_metric(target, middleware="auth") == 1
        self.client.get("/", headers = { "Authorization": f"Bearer {self.token}" })
        assert self.get_metric(target, middleware="auth") == 1
    @loverride_settings
    def test_middleware_wrong_token_per_config (self):
        target = "stateless_auth_middleware_run_per_config_wrong_token_total"
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/")
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/", headers = { "Authorization": "HHH" })
        assert self.get_metric(target, middleware="auth") is None
        self.client.get("/", headers = { "Authorization": "Bearer HHH" })
        assert self.get_metric(target, middleware="auth") == 1
        self.client.get("/", headers = { "Authorization": f"Bearer {self.token}" })
        assert self.get_metric(target, middleware="auth") == 1

    @loverride_settings
    def test_encode_metrics (self):
        target1 = "stateless_auth_encode_total"
        target2 = "stateless_auth_encode_latency_bucket"
        target3 = "stateless_auth_encode_total_per_engine_total"
        target4 = "stateless_auth_encode_latency_per_engine_bucket"

        assert self.get_metric(target1) == 0
        assert self.get_metric(target3, engine="default") is None
        assert self.get_bucket_metric(target2).greater_or_equal( _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS)) )
        assert self.get_bucket_metric(target4, engine="default").greater_or_equal( _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS)) )
        self.client.get("/account/acquire/?username=user&password=wrong")
        assert self.get_metric(target1) == 0
        assert self.get_metric(target3, engine="default") is None
        assert self.get_bucket_metric(target2).greater_or_equal( _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS)) )
        assert self.get_bucket_metric(target4, engine="default").greater_or_equal( _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS)) )
        self.client.get("/account/acquire/?username=user&password=user")
        assert self.get_metric(target1) == 1
        assert self.get_metric(target3, engine="default") == 1
        assert self.get_bucket_metric(target2).greater_or_equal( self.get_metric_of_latency(0.25) )
        assert self.get_bucket_metric(target4, engine="default").greater_or_equal( self.get_metric_of_latency(0.25) )
    @loverride_settings
    def test_decode_metrics (self):
        def test_tlm (name: str, adv: List[float]):
            v0 = _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS))
            for x in adv:
                v0 = v0.add( self.get_metric_of_latency(x) )
            v1 = len(adv)
            v2 = v1
            if v2 == 0: v2 = None

            assert self.get_metric( name + "_total" ) == v1
            assert self.get_metric( name + "_total_per_engine_total", engine="default" ) == v2
            assert self.get_bucket_metric( name + "_latency_bucket" ).greater_or_equal( v0 )
            assert self.get_bucket_metric( name + "_latency_per_engine_bucket", engine="default" ).greater_or_equal( v0 )
        test_tlm( "stateless_auth_decode",         [] )
        test_tlm( "stateless_auth_decode_success", [] )
        test_tlm( "stateless_auth_decode_failed",  [] )
        self.client.get("/")
        test_tlm( "stateless_auth_decode",         [] )
        test_tlm( "stateless_auth_decode_success", [] )
        test_tlm( "stateless_auth_decode_failed",  [] )
        self.client.get("/", headers = { "Authorization": "HHH" })
        test_tlm( "stateless_auth_decode",         [] )
        test_tlm( "stateless_auth_decode_success", [] )
        test_tlm( "stateless_auth_decode_failed",  [] )
        self.client.get("/", headers = { "Authorization": "Bearer HHH" })
        test_tlm( "stateless_auth_decode",         [ 0.25 ] )
        test_tlm( "stateless_auth_decode_success", [] )
        test_tlm( "stateless_auth_decode_failed",  [ 0.25 ] )
        self.client.get("/", headers = { "Authorization": f"Bearer {self.token}" })
        test_tlm( "stateless_auth_decode",         [ 0.25, 0.25 ] )
        test_tlm( "stateless_auth_decode_success", [ 0.25 ] )
        test_tlm( "stateless_auth_decode_failed",  [ 0.25 ] )
    @loverride_settings
    def test_acquire_acquire (self):
        def __request (target: str):
            factory = RequestFactory()
            request = factory.get(target)
            self.engine2.acquire_view(request)
        def test_tlm (name: str, adv: List[float]):
            v0 = _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS))
            for x in adv:
                v0 = v0.add( self.get_metric_of_latency(x) )
            v1 = len(adv)
            v2 = v1
            if v2 == 0: v2 = None

            assert self.get_metric( name + "_total" ) == v1
            assert self.get_metric( name + "_total_per_engine_total", engine="engine2" ) == v2
            assert self.get_bucket_metric( name + "_latency_bucket" ).greater_or_equal( v0 )
            assert self.get_bucket_metric( name + "_latency_per_engine_bucket", engine="engine2" ).greater_or_equal( v0 )
        test_tlm("stateless_auth_acquire_engine_acquire_view", [])
        test_tlm("stateless_auth_acquire_engine_acquire_view_success", [])
        test_tlm("stateless_auth_acquire_engine_acquire_view_failed", [])
        __request("/account/acquire/")
        test_tlm("stateless_auth_acquire_engine_acquire_view",         [ 0.005 ])
        test_tlm("stateless_auth_acquire_engine_acquire_view_success", [])
        test_tlm("stateless_auth_acquire_engine_acquire_view_failed",  [ 0.005 ])
        __request("/account/acquire/?username=user4&password=user")
        test_tlm("stateless_auth_acquire_engine_acquire_view",         [ 0.005, 0.2 ])
        test_tlm("stateless_auth_acquire_engine_acquire_view_success", [])
        test_tlm("stateless_auth_acquire_engine_acquire_view_failed",  [ 0.005, 0.2 ])
        __request("/account/acquire/?username=user&password=user")
        test_tlm("stateless_auth_acquire_engine_acquire_view",         [ 0.005, 0.2, 0.4 ])
        test_tlm("stateless_auth_acquire_engine_acquire_view_success", [ 0.4 ])
        test_tlm("stateless_auth_acquire_engine_acquire_view_failed",  [ 0.005, 0.2 ])
    @loverride_settings
    def test_refresh_acquire (self):
        def __request (target: str):
            factory = RequestFactory()
            request = factory.get(target)
            self.engine1.acquire_view(request)
        def test_tlm (name: str, adv: List[float]):
            v0 = _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS))
            for x in adv:
                v0 = v0.add( self.get_metric_of_latency(x) )
            v1 = len(adv)
            v2 = v1
            if v2 == 0: v2 = None

            assert self.get_metric( name + "_total" ) == v1
            assert self.get_metric( name + "_total_per_engine_total", engine="engine1" ) == v2
            assert self.get_bucket_metric( name + "_latency_bucket" ).greater_or_equal( v0 )
            assert self.get_bucket_metric( name + "_latency_per_engine_bucket", engine="engine1" ).greater_or_equal( v0 )
        test_tlm("stateless_auth_refresh_engine_acquire_view", [])
        test_tlm("stateless_auth_refresh_engine_acquire_view_success", [])
        test_tlm("stateless_auth_refresh_engine_acquire_view_failed", [])
        __request("/account/acquire/")
        test_tlm("stateless_auth_refresh_engine_acquire_view",         [ 0.005 ])
        test_tlm("stateless_auth_refresh_engine_acquire_view_success", [])
        test_tlm("stateless_auth_refresh_engine_acquire_view_failed",  [ 0.005 ])
        __request("/account/acquire/?username=user4&password=user")
        test_tlm("stateless_auth_refresh_engine_acquire_view",         [ 0.005, 0.2 ])
        test_tlm("stateless_auth_refresh_engine_acquire_view_success", [])
        test_tlm("stateless_auth_refresh_engine_acquire_view_failed",  [ 0.005, 0.2 ])
        __request("/account/acquire/?username=user&password=user")
        test_tlm("stateless_auth_refresh_engine_acquire_view",         [ 0.005, 0.2, 0.4 ])
        test_tlm("stateless_auth_refresh_engine_acquire_view_success", [ 0.4 ])
        test_tlm("stateless_auth_refresh_engine_acquire_view_failed",  [ 0.005, 0.2 ])
    @loverride_settings
    def test_refresh_refresh (self):
        def __request (header = None):
            factory = RequestFactory()
            request = factory.get("/", headers={} if header is None else { 'Refresh' : header })
            self.engine1.refresh_view(request)
        def test_tlm (name: str, adv: List[float]):
            v0 = _Vector([0] * len(PROMETHEUS_LATENCY_BUCKETS))
            for x in adv:
                v0 = v0.add( self.get_metric_of_latency(x) )
            v1 = len(adv)
            v2 = v1
            if v2 == 0: v2 = None

            assert self.get_metric( name + "_total" ) == v1
            assert self.get_metric( name + "_total_per_engine_total", engine="engine1" ) == v2
            assert self.get_bucket_metric( name + "_latency_bucket" ).greater_or_equal( v0 )
            assert self.get_bucket_metric( name + "_latency_per_engine_bucket", engine="engine1" ).greater_or_equal( v0 )
        test_tlm("stateless_auth_refresh_engine_refresh_view",         [])
        test_tlm("stateless_auth_refresh_engine_refresh_view_success", [])
        test_tlm("stateless_auth_refresh_engine_refresh_view_missing", [])
        test_tlm("stateless_auth_refresh_engine_refresh_view_expired", [])
        test_tlm("stateless_auth_refresh_engine_refresh_view_wrong",   [])
        __request(None)
        test_tlm("stateless_auth_refresh_engine_refresh_view",         [ 0.005 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_success", [])
        test_tlm("stateless_auth_refresh_engine_refresh_view_missing", [ 0.005 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_expired", [])
        test_tlm("stateless_auth_refresh_engine_refresh_view_wrong",   [])
        __request("RANDOM TOKEN")
        test_tlm("stateless_auth_refresh_engine_refresh_view",         [ 0.005, 0.2 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_success", [])
        test_tlm("stateless_auth_refresh_engine_refresh_view_missing", [ 0.005 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_expired", [])
        test_tlm("stateless_auth_refresh_engine_refresh_view_wrong",   [ 0.2 ])

        token1 = self.engine1.encode( User.from_user(self.user) )
        __request(token1)
        test_tlm("stateless_auth_refresh_engine_refresh_view",         [ 0.005, 0.2, 0.4 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_success", [ 0.4 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_missing", [ 0.005 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_expired", [ ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_wrong",   [ 0.2 ])
        token3 = self.engine3.encode( User.from_user(self.user) )
        __request(token3)
        test_tlm("stateless_auth_refresh_engine_refresh_view",         [ 0.005, 0.2, 0.4, 0.2 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_success", [ 0.4 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_missing", [ 0.005 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_expired", [ 0.2 ])
        test_tlm("stateless_auth_refresh_engine_refresh_view_wrong",   [ 0.2 ])