import sys
import unittest

sys.path.append("../../")

from jstreams.ioc import injector

tc = unittest.TestCase()
tc.assertEqual(injector().get_active_profile(), "testProfile")
tc.assertEqual(injector().find_var(int, "test"), 1)
tc.assertIsNone(injector().find_var(str, "other_value"))
