from jstreams import resolveDependencies
from jstreams.ioc import service
from mockService1 import MockService1
from mockService2 import MockService2


@service()
@resolveDependencies({"mockService1": MockService1, "mockService2": MockService2})
class MockService3:
    mockService1: MockService1
    mockService2: MockService2

    def getMockService1Class(self) -> type:
        return type(self.mockService1)

    def getMockService2Class(self) -> type:
        return type(self.mockService2)
