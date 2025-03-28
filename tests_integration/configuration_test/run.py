import sys
import unittest

sys.path.append("../../")

from jstreams.ioc import injector

tc = unittest.TestCase()

injector().scan_modules(["config"])
injector().activate_profile("profile1")

tc.assertEqual(injector().find(str), "test1")
tc.assertEqual(injector().find(int), 3)

tc.assertEqual(injector().find_var(str, "test1"), "test1")
tc.assertEqual(injector().find_var(str, "test2"), "test2")
