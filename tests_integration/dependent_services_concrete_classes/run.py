import sys

sys.path.append("../../")

from jstreams.ioc import injector
from mockService3 import MockService3

ms3 = injector().find(MockService3)

print("Checking ms3")
assert ms3 is not None
print("Checking ms1")
assert ms3.mockService1 is not None
print("Checking ms2")
assert ms3.mockService2 is not None
