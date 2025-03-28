from jstreams import resolve_dependencies
from jstreams.ioc import service
from iMockService1 import IMockService
from mockService2 import MockService2


@service()
@resolve_dependencies({"mockService1": IMockService, "mockService2": MockService2})
class MockService3:
    mockService1: IMockService
    mockService2: MockService2

    def getMockService1Class(self) -> type:
        return type(self.mockService1)

    def getMockService2Class(self) -> type:
        return type(self.mockService2)
