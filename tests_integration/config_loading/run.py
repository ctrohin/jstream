import sys
import unittest

sys.path.append("../../")

from jstreams.ioc import injector

tc = unittest.TestCase()
tc.assertEqual(injector().get_active_profile(), "testProfile")
