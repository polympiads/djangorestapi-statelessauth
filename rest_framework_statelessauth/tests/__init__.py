
from django.test import TestCase

from rest_framework_statelessauth.tests.wire \
    import CustomAuthWireTestCases, DefaultAuthWireTestCases, \
        AuthPermissionTests, AuthGroupTests, AuthUserTests
from rest_framework_statelessauth.tests.config import ConfigTestCases
from rest_framework_statelessauth.tests.engine \
    import AbstractEngineTestCases, AcquireEngineTestCases, RefreshEngineTestCases

class InitialTestCases (TestCase):
    def test_initial(self):
        assert 1 == 1
