from jstreams import resolveDependencies
from jstreams.ioc import service
from mockService1 import MockService1


@service()
@resolveDependencies({"mockService1": MockService1})
class MockService2:
    mockService1: MockService1

    def getMockService1Class(self) -> type:
        return type(self.mockService1)
