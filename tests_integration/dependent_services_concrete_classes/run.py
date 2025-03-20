import sys
import unittest

sys.path.append("../../")

from jstreams.ioc import injector
from mockService3 import MockService3

tc = unittest.TestCase()

ms3 = injector().find(MockService3)

tc.assertIsNotNone(ms3, "Service3 should have been injected")
tc.assertIsNotNone(ms3.mockService1, "Service1 should have been injected")
tc.assertIsNotNone(ms3.mockService2, "Service2 should have been injected")
