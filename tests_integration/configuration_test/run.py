import sys
import unittest

sys.path.append("../../")

from jstreams.ioc import injector

tc = unittest.TestCase()

injector().scanModules(["config"])
injector().activateProfile("profile1")

tc.assertEqual(injector().find(str), "test1")
tc.assertEqual(injector().find(int), 3)
