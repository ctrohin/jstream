from jstreams import resolve_dependencies
from jstreams.ioc import service
from iMockService1 import IMockService


@service()
@resolve_dependencies({"mockService1": IMockService})
class MockService2:
    mockService1: IMockService

    def getMockService1Class(self) -> type:
        return type(self.mockService1)
