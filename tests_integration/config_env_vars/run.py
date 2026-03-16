import sys
import unittest
import os

sys.path.append("../../")
# Simulate a variable environment that is not set by anywhere in the container
os.environ["configured_value"] = "test"
# Simulate overridding an already set variable by providing a value via the env variables
os.environ["override_value"] = "overridden"
from jstreams.ioc import injector

injector().provide_var(str, "override_value", "not_overridden")
tc = unittest.TestCase()
tc.assertIsNone(injector().find_var(str, "missing_configured_value"))
tc.assertEqual(injector().find_var(str, "configured_value"), "test")
tc.assertEqual(injector().find_var(str, "override_value"), "overridden")
