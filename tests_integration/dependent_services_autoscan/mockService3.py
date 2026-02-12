from jstreams import resolve_dependencies
from jstreams.ioc import service
from interfaces import IMockService1, IMockService2, IMockService3


@service(IMockService3)
@resolve_dependencies({"mockService1": IMockService1, "mockService2": IMockService2})
class MockService3:
    mockService1: IMockService1
    mockService2: IMockService2

    def getMockService1Class(self) -> type:
        return type(self.mockService1)

    def getMockService2Class(self) -> type:
        return type(self.mockService2)
