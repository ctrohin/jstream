from jstreams import resolve_dependencies
from jstreams.ioc import service
from mocks.ioc.mockService1 import MockService1


@service()
@resolve_dependencies({"mockService1": MockService1})
class MockService2:
    mockService1: MockService1

    def getMockService1Class(self) -> type:
        return type(self.mockService1)
