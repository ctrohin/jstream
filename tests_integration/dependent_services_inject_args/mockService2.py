from jstreams import resolveDependencies
from jstreams.ioc import service
from iMockService1 import IMockService


@service()
@resolveDependencies({"mockService1": IMockService})
class MockService2:
    mockService1: IMockService

    def getMockService1Class(self) -> type:
        return type(self.mockService1)
