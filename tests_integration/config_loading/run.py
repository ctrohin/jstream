import sys
import unittest

sys.path.append("../../")

from jstreams.ioc import injector

tc = unittest.TestCase()
tc.assertEqual(injector().get_active_profile(), "testProfile")
tc.assertEqual(injector().find_var(int, "test"), 1)
tc.assertIsNone(injector().find_var(str, "other_value"))
tc.assertEqual(injector().find_var(str, "test2.var1"), "test")
tc.assertEqual(injector().find_var(int, "test2.var2"), 10)
tc.assertEqual(injector().find_var(str, "test2.var3.var31"), "test31")
tc.assertEqual(injector().find_var(list, "test2.listVar"), [1, 2, 3])
