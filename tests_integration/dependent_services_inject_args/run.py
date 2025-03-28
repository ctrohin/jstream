import sys
import unittest

sys.path.append("../../")

from jstreams.ioc import injector
from mockService3 import MockService3

tc = unittest.TestCase()
injector().scan_modules(["mockService1"])
injector().provide_var(str, "var1", "var1Value")
ms3 = injector().find(MockService3)

tc.assertIsNotNone(ms3, "Service3 should have been injected")
tc.assertIsNotNone(ms3.mockService1, "Service 1 should have been injected")
tc.assertIsNotNone(ms3.mockService2, "Service 2 should have been injected")
tc.assertEqual(ms3.var1, "var1Value", "Variable should have been injected")
