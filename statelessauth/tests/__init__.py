
from django.test import TestCase

from statelessauth.tests.wire \
    import CustomAuthWireTestCases, DefaultAuthWireTestCases, \
        AuthPermissionTests, AuthGroupTests, AuthUserTests
from statelessauth.tests.config import ConfigTestCases
from statelessauth.tests.engine \
    import AbstractEngineTestCases, AcquireEngineTestCases, RefreshEngineTestCases
from statelessauth.tests.middlewares import MiddlewareTestCases
from statelessauth.tests.prometheus import PrometheusMetricsTest

class InitialTestCases (TestCase):
    def test_initial(self):
        assert 1 == 1
