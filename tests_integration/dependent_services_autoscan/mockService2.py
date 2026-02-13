from calendar import c
from jstreams import resolve_dependencies
from jstreams.ioc import service
from interfaces import IMockService1, IMockService2


@service(class_name=IMockService2)
@resolve_dependencies({"mockService1": IMockService1})
class MockService2:
    mockService1: IMockService1

    def getMockService1Class(self) -> type:
        return type(self.mockService1)
